from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from decimal import Decimal, InvalidOperation

from .models import (
    Fee,
    Payment,
    PaymentMethod,
    MpesaTransaction,
)

from .services.mpesa import MpesaService

from accounts.models import Student, Parent

from .serializers import (
    SimpleStudentSerializer,
    SimpleParentSerializer,
    SimplePaymentSerializer,
    FeeSerializer,
    PaymentSerializer,
    PaymentMethodSerializer,
)

from accounts.permissions import IsAdminOrBursar


# ==========================================================
# STUDENTS
# ==========================================================

class SimpleStudentViewSet(ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = SimpleStudentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Admin can see all students
        if user.role == "admin":
            return Student.objects.all()

        # Bursar can see all students for finance management
        if user.role == "bursar":
            return Student.objects.all()

        # Parent can see their own children
        if user.role == "parent":
            return user.parent_profile.students.all()

        # Student can see their own profile
        if user.role == "student":
            return Student.objects.filter(
                id=user.student_profile.id
            )

        return Student.objects.none()


# ==========================================================
# PARENTS
# ==========================================================

class SimpleParentViewSet(ModelViewSet):
    queryset = Parent.objects.all()
    serializer_class = SimpleParentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Admin can see all parents
        if user.role == "admin":
            return Parent.objects.all()

        # Bursar can see parents for finance management
        if user.role == "bursar":
            return Parent.objects.all()

        # Parent can see their own profile
        if user.role == "parent":
            return Parent.objects.filter(
                id=user.parent_profile.id
            )

        return Parent.objects.none()


# ==========================================================
# FEES
# ==========================================================

class FeeViewSet(ModelViewSet):
    serializer_class = FeeSerializer
    queryset = Fee.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Admin
        if user.role == "admin":
            return Fee.objects.all()

        # Bursar
        if user.role == "bursar":
            return Fee.objects.all()

        # Parent
        if user.role == "parent":
            return Fee.objects.filter(
                student__in=user.parent_profile.students.all()
            )

        # Student
        if user.role == "student":
            return Fee.objects.filter(
                student=user.student_profile
            )

        return Fee.objects.none()

    def perform_create(self, serializer):
        user = self.request.user

        # Only Admin and Bursar can create fees
        if user.role not in ["admin", "bursar"]:
            raise PermissionDenied(
                "You do not have permission to create fee records."
            )

        serializer.save()


# ==========================================================
# PAYMENTS
# ==========================================================

class PaymentViewSet(ModelViewSet):
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Admin
        if user.role == "admin":
            return Payment.objects.all()

        # Bursar
        if user.role == "bursar":
            return Payment.objects.all()

        # Parent
        if user.role == "parent":
            return Payment.objects.filter(
                parent=user.parent_profile
            )

        # Student
        if user.role == "student":
            return Payment.objects.filter(
                student=user.student_profile
            )

        return Payment.objects.none()

    def perform_create(self, serializer):
        user = self.request.user

        # ==================================================
        # PARENT PAYMENT
        # ==================================================

        if user.role == "parent":
            student = serializer.validated_data["student"]

            if student not in user.parent_profile.students.all():
                raise PermissionDenied(
                    "You cannot pay for this student."
                )

            serializer.save(
                parent=user.parent_profile,
                status="pending",
            )

            return

        # ==================================================
        # ADMIN / BURSAR PAYMENT
        # ==================================================

        if user.role in ["admin", "bursar"]:
            serializer.save()
            return

        raise PermissionDenied(
            "You do not have permission to create payment records."
        )


# ==========================================================
# PAYMENT METHODS
# ==========================================================

class PaymentMethodViewSet(ModelViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer

    # Only Admin and Bursar should manage payment methods
    permission_classes = [IsAdminOrBursar]

# ==========================================================
# BURSAR DASHBOARD
# ==========================================================

class BursarDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Only Admin and Bursar can access the finance dashboard
        if user.role not in ["admin", "bursar"]:
            return Response(
                {
                    "detail": (
                        "You do not have permission to "
                        "access the finance dashboard."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # --------------------------------------------------
        # TOTAL FEES
        # --------------------------------------------------

        total_fees = (
            Fee.objects.aggregate(
                total=Sum("total_amount")
            )["total"]
            or Decimal("0.00")
        )

        # --------------------------------------------------
        # TOTAL SUCCESSFUL PAYMENTS
        # --------------------------------------------------

        total_collected = (
            Payment.objects.filter(
                status="successful"
            ).aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        # --------------------------------------------------
        # OUTSTANDING
        # --------------------------------------------------

        outstanding = total_fees - total_collected

        if outstanding < 0:
            outstanding = Decimal("0.00")

        # --------------------------------------------------
        # COLLECTION PERCENTAGE
        # --------------------------------------------------

        if total_fees > 0:
            collection_percentage = (
                total_collected / total_fees
            ) * Decimal("100")
        else:
            collection_percentage = Decimal("0.00")

        # --------------------------------------------------
        # PAYMENT METHODS
        # --------------------------------------------------

        mpesa_collected = (
            Payment.objects.filter(
                status="successful",
                method__name="mpesa"
            ).aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        cash_collected = (
            Payment.objects.filter(
                status="successful",
                method__name="cash"
            ).aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        bank_collected = (
            Payment.objects.filter(
                status="successful",
                method__name="bank"
            ).aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        # --------------------------------------------------
        # PAYMENT METHOD PERCENTAGES
        # --------------------------------------------------

        if total_collected > 0:

            mpesa_percentage = (
                mpesa_collected / total_collected
            ) * Decimal("100")

            cash_percentage = (
                cash_collected / total_collected
            ) * Decimal("100")

            bank_percentage = (
                bank_collected / total_collected
            ) * Decimal("100")

        else:
            mpesa_percentage = Decimal("0.00")
            cash_percentage = Decimal("0.00")
            bank_percentage = Decimal("0.00")

        # --------------------------------------------------
        # STUDENTS WITH OUTSTANDING BALANCES
        # --------------------------------------------------

        students_with_balance = 0

        for fee in Fee.objects.select_related(
            "student"
        ).all():

            if fee.balance() > 0:
                students_with_balance += 1

        # --------------------------------------------------
        # TODAY'S TRANSACTIONS
        # --------------------------------------------------

        from django.utils import timezone

        today = timezone.localdate()

        transactions_today = Payment.objects.filter(
            created_at__date=today
        ).count()

        # --------------------------------------------------
        # PENDING PAYMENTS
        # --------------------------------------------------

        pending_payments = Payment.objects.filter(
            status="pending"
        ).count()

        # --------------------------------------------------
        # RECENT PAYMENTS
        # --------------------------------------------------

        recent_payments = (
            Payment.objects
            .select_related(
                "student__user",
                "method",
                "fee",
            )
            .order_by("-created_at")[:10]
        )

        recent_payment_data = []

        for payment in recent_payments:

            student = payment.student
            user = student.user

            recent_payment_data.append(
                {
                    "id": payment.id,

                    "student_name": (
                        user.get_full_name()
                        or user.username
                    ),

                    "admission_number": (
                        student.admission_number
                        or "—"
                    ),

                    "school_class": (
                        str(student.school_class)
                        if student.school_class
                        else "—"
                    ),

                    "amount": str(payment.amount),

                    "method": (
                        payment.method.name
                        if payment.method
                        else "—"
                    ),

                    "status": payment.status,

                    "transaction_id": (
                        payment.transaction_id
                        or "—"
                    ),

                    "created_at": payment.created_at.isoformat(),
                }
            )

        # --------------------------------------------------
        # RESPONSE
        # --------------------------------------------------

        return Response(
            {
                "total_fees": str(total_fees),
                "total_collected": str(
                    total_collected
                ),
                "outstanding": str(
                    outstanding
                ),

                "collection_percentage": round(
                    float(collection_percentage),
                    2
                ),

                "mpesa_collected": str(
                    mpesa_collected
                ),

                "cash_collected": str(
                    cash_collected
                ),

                "bank_collected": str(
                    bank_collected
                ),

                "mpesa_percentage": round(
                    float(mpesa_percentage),
                    2
                ),

                "cash_percentage": round(
                    float(cash_percentage),
                    2
                ),

                "bank_percentage": round(
                    float(bank_percentage),
                    2
                ),

                "students_with_balance": (
                    students_with_balance
                ),

                "transactions_today": (
                    transactions_today
                ),

                "pending_payments": (
                    pending_payments
                ),

                "recent_payments": (
                    recent_payment_data
                ),
            }
        )
# ==========================================================
# M-PESA STK PUSH
# ==========================================================

class MpesaSTKPushView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # ==================================================
        # ONLY PARENTS CAN INITIATE STK PUSH
        # ==================================================

        if user.role != "parent":
            return Response(
                {
                    "error": (
                        "Only parents can initiate "
                        "M-Pesa payments."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        student_id = request.data.get("student_id")
        fee_id = request.data.get("fee_id")
        amount_value = request.data.get("amount")
        phone_number = request.data.get("phone_number")

        # ==================================================
        # REQUIRED FIELDS
        # ==================================================

        if not all(
            [
                student_id,
                fee_id,
                amount_value,
                phone_number,
            ]
        ):
            return Response(
                {
                    "error": "All payment fields are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ==================================================
        # CONVERT AMOUNT
        # ==================================================

        try:
            amount = Decimal(str(amount_value))

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            return Response(
                {
                    "error": "Invalid payment amount."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount <= 0:
            return Response(
                {
                    "error": "Amount must be greater than zero."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        parent = user.parent_profile

        # ==================================================
        # VERIFY STUDENT BELONGS TO PARENT
        # ==================================================

        try:
            student = parent.students.get(
                id=student_id
            )

        except Student.DoesNotExist:
            return Response(
                {
                    "error": (
                        "This student does not belong to you."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ==================================================
        # GET FEE
        # ==================================================

        try:
            fee = Fee.objects.get(
                id=fee_id,
                student=student,
            )

        except Fee.DoesNotExist:
            return Response(
                {
                    "error": "Fee record not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ==================================================
        # CHECK BALANCE
        # ==================================================

        if amount > fee.balance():
            return Response(
                {
                    "error": (
                        "Amount exceeds fee balance."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ==================================================
        # GET M-PESA PAYMENT METHOD
        # ==================================================

        mpesa_method, created = (
            PaymentMethod.objects.get_or_create(
                name="mpesa"
            )
        )

        # ==================================================
        # CREATE PENDING PAYMENT
        # ==================================================

        payment = Payment.objects.create(
            student=student,
            parent=parent,
            fee=fee,
            amount=amount,
            method=mpesa_method,
            status="pending",
        )

        # ==================================================
        # SEND STK PUSH
        # ==================================================

        try:
            result = MpesaService.stk_push(
                phone_number=phone_number,
                amount=amount,
                account_reference=f"FEE-{fee.id}",
                transaction_desc="School Fees",
            )

        except Exception as e:
            payment.status = "failed"
            payment.save()

            return Response(
                {
                    "error": (
                        "Unable to initiate "
                        "M-Pesa payment."
                    ),
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # ==================================================
        # CREATE MPESA TRANSACTION
        # ==================================================

        mpesa_transaction = (
            MpesaTransaction.objects.create(
                payment=payment,
                phone_number=phone_number,
                checkout_request_id=result.get(
                    "CheckoutRequestID"
                ),
                merchant_request_id=result.get(
                    "MerchantRequestID"
                ),
                amount=amount,
                status="pending",
            )
        )

        # ==================================================
        # RESPONSE
        # ==================================================

        return Response(
            {
                "message": (
                    "STK Push sent to your phone."
                ),
                "payment_id": payment.id,
                "mpesa_transaction_id": (
                    mpesa_transaction.id
                ),
                "checkout_request_id": (
                    result.get("CheckoutRequestID")
                ),
            },
            status=status.HTTP_201_CREATED,
        )


# ==========================================================
# M-PESA CALLBACK
# ==========================================================

class MpesaCallbackView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        data = request.data

        # ==================================================
        # GET CALLBACK
        # ==================================================

        callback = (
            data.get("Body", {})
            .get("stkCallback", {})
        )

        checkout_request_id = callback.get(
            "CheckoutRequestID"
        )

        merchant_request_id = callback.get(
            "MerchantRequestID"
        )

        result_code = callback.get(
            "ResultCode"
        )

        result_description = callback.get(
            "ResultDesc"
        )

        print("\n")
        print("========================================")
        print("        M-PESA CALLBACK RECEIVED")
        print("========================================")
        print(
            "CheckoutRequestID:",
            checkout_request_id,
        )
        print(
            "MerchantRequestID:",
            merchant_request_id,
        )
        print("ResultCode:", result_code)
        print(
            "ResultDesc:",
            result_description,
        )
        print("========================================")
        print("\n")

        # ==================================================
        # VALIDATE CALLBACK
        # ==================================================

        if not checkout_request_id:
            print(
                "M-PESA ERROR: "
                "Missing CheckoutRequestID"
            )

            return Response(
                {
                    "message": "Invalid callback."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if result_code is None:
            print(
                "M-PESA ERROR: "
                "Missing ResultCode"
            )

            return Response(
                {
                    "message": (
                        "Invalid callback result."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ==================================================
        # CONVERT RESULT CODE
        # ==================================================

        try:
            result_code = int(result_code)

        except (TypeError, ValueError):
            print(
                "M-PESA ERROR: "
                "Invalid ResultCode:",
                result_code,
            )

            return Response(
                {
                    "message": "Invalid ResultCode."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ==================================================
        # FIND TRANSACTION
        # ==================================================

        try:
            transaction = (
                MpesaTransaction.objects
                .select_related("payment")
                .get(
                    checkout_request_id=(
                        checkout_request_id
                    )
                )
            )

        except MpesaTransaction.DoesNotExist:
            print(
                "M-PESA ERROR: "
                "Transaction not found:",
                checkout_request_id,
            )

            return Response(
                {
                    "message": (
                        "Transaction not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ==================================================
        # DUPLICATE PROTECTION
        # ==================================================

        if transaction.status == "successful":
            print(
                "M-PESA: Transaction "
                "already successful:",
                checkout_request_id,
            )

            return Response(
                {
                    "message": (
                        "Transaction already processed."
                    )
                },
                status=status.HTTP_200_OK,
            )

        # ==================================================
        # SAVE CALLBACK RESULT
        # ==================================================

        transaction.result_code = str(
            result_code
        )

        transaction.result_description = (
            result_description
        )

        if merchant_request_id:
            transaction.merchant_request_id = (
                merchant_request_id
            )

        # ==================================================
        # SUCCESSFUL PAYMENT
        # ==================================================

        if result_code == 0:
            print("M-PESA RESULT: SUCCESS")

            callback_metadata = (
                callback
                .get("CallbackMetadata", {})
                .get("Item", [])
            )

            receipt_number = None
            phone_number = None
            amount = None
            transaction_date = None

            for item in callback_metadata:
                name = item.get("Name")
                value = item.get("Value")

                if name == "MpesaReceiptNumber":
                    receipt_number = value

                elif name == "PhoneNumber":
                    phone_number = value

                elif name == "Amount":
                    amount = value

                elif name == "TransactionDate":
                    transaction_date = value

            print(
                "Receipt:",
                receipt_number,
            )

            print(
                "Phone:",
                phone_number,
            )

            print(
                "Amount:",
                amount,
            )

            print(
                "TransactionDate:",
                transaction_date,
            )

            # ==================================================
            # RECEIPT REQUIRED
            # ==================================================

            if not receipt_number:
                print(
                    "M-PESA ERROR: "
                    "Successful callback has no "
                    "receipt number."
                )

                transaction.status = "failed"
                transaction.save()

                payment = transaction.payment
                payment.status = "failed"
                payment.save()

                return Response(
                    {
                        "message": (
                            "Callback received without "
                            "M-Pesa receipt."
                        )
                    },
                    status=status.HTTP_200_OK,
                )

            # ==================================================
            # CHECK DUPLICATE RECEIPT
            # ==================================================

            duplicate = (
                MpesaTransaction.objects
                .filter(
                    mpesa_receipt_number=receipt_number
                )
                .exclude(
                    id=transaction.id
                )
                .exists()
            )

            if duplicate:
                print(
                    "M-PESA ERROR: "
                    "Duplicate receipt:",
                    receipt_number,
                )

                return Response(
                    {
                        "message": (
                            "M-Pesa receipt already "
                            "processed."
                        )
                    },
                    status=status.HTTP_200_OK,
                )

            # ==================================================
            # SAVE RECEIPT
            # ==================================================

            transaction.mpesa_receipt_number = (
                receipt_number
            )

            transaction.status = "successful"
            transaction.save()

            # ==================================================
            # UPDATE PAYMENT
            # ==================================================

            payment = transaction.payment

            payment.status = "successful"

            payment.transaction_id = (
                receipt_number
            )

            payment.save()

            print(
                "========================================"
            )

            print(
                "M-PESA PAYMENT SUCCESSFUL"
            )

            print(
                "Receipt:",
                receipt_number,
            )

            print(
                "Payment ID:",
                payment.id,
            )

            print(
                "========================================"
            )

            print("\n")

        # ==================================================
        # FAILED / CANCELLED PAYMENT
        # ==================================================

        else:
            print(
                "M-PESA RESULT: FAILED"
            )

            print(
                "ResultCode:",
                result_code,
            )

            print(
                "ResultDesc:",
                result_description,
            )

            transaction.status = "failed"
            transaction.save()

            payment = transaction.payment

            payment.status = "failed"
            payment.save()

            print(
                "========================================"
            )

            print(
                "M-PESA PAYMENT FAILED"
            )

            print(
                "ResultCode:",
                result_code,
            )

            print(
                "ResultDesc:",
                result_description,
            )

            print(
                "Payment ID:",
                payment.id,
            )

            print(
                "========================================"
            )

            print("\n")

        # ==================================================
        # ACKNOWLEDGE CALLBACK
        # ==================================================

        return Response(
            {
                "message": "Callback processed."
            },
            status=status.HTTP_200_OK,
        )


