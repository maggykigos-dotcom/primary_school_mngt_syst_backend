from rest_framework import serializers
from .models import Fee, Payment, PaymentMethod,  MpesaTransaction

from accounts.models import Student, Parent


# # -------------------------
# # # SIMPLE STUDENT
# # -------------------------
class SimpleStudentSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        source="user.first_name",
        read_only=True
    )

    last_name = serializers.CharField(
        source="user.last_name",
        read_only=True
    )

    grade_name = serializers.SerializerMethodField()

    school_class_name = serializers.SerializerMethodField()

    class Meta:
        model = Student

        fields = [
            "id",
            "admission_number",
            "first_name",
            "last_name",
            "grade_name",
            "school_class_name",
        ]

    def get_grade_name(self, obj):
        if obj.school_class and obj.school_class.grade:
            return obj.school_class.grade.name

        return "—"

    def get_school_class_name(self, obj):
        if obj.school_class:
            return obj.school_class.name

        return "—"  
    # first_name = serializers.CharField(
    #     source="user.first_name",
    #     read_only=True
    # )
    # last_name = serializers.CharField(
    #     source="user.last_name",
    #     read_only=True
    # )

    # class Meta:
    #     model = Student
    #     fields = [
    #         "id",
    #         "admission_number",
    #         "first_name",
    #         "last_name",
    #     ]

# # # -------------------------
# # # SIMPLE PARENT 

class SimpleParentSerializer(serializers.ModelSerializer):
    parent_name = serializers.SerializerMethodField()

    class Meta:
        model = Parent
        fields = ['id', 'parent_name']

    def get_parent_name(self, obj):
        if obj.user:
            return obj.user.get_full_name()
        return ""

class SimplePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
       
        fields = ['id', 'amount', 'created_at']



class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id','name']


# PAYMENT SERIALIZER
# -------------------------
class PaymentSerializer(serializers.ModelSerializer):
    student = SimpleStudentSerializer(read_only=True)
    parent = SimpleParentSerializer(read_only=True)
    method = PaymentMethodSerializer(read_only=True)
    fee = serializers.PrimaryKeyRelatedField(queryset=Fee.objects.all())

    # For writing (POST)
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), write_only=True, source='student'
    )
    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Parent.objects.all(), write_only=True, source='parent'
    )
    fee_id = serializers.PrimaryKeyRelatedField(
        queryset=Fee.objects.all(), write_only=True, source='fee'
    )
    method_id = serializers.PrimaryKeyRelatedField(
        queryset=PaymentMethod.objects.all(), write_only=True, source='method'
    )

    class Meta:
        model = Payment
        fields = [
            'id',
            'student',
            'parent',
            'fee',
            'amount',
            'method',
            'transaction_id',
            'status',
            'created_at',
            'parent_id',
            'student_id', 
            'fee_id',
            'method_id',
        ]

        read_only_fields = [
            'id',
            'parent',
            'student',
            'fee',
            'method',
            'status',
            'created_at',
        ]
        

    def validate(self, data):
        student = data.get('student')
        parent = data.get('parent')
        fee = data.get('fee')
        amount = data.get('amount')

        # Parent owns student
        if student not in parent.students.all():
            raise serializers.ValidationError("This student does not belong to this parent")

        # Fee belongs to student
        if fee.student != student:
            raise serializers.ValidationError("This fee does not belong to this student")

        # Prevent overpayment
        if fee.balance() < amount:
            raise serializers.ValidationError("Payment exceeds remaining balance")

        return data
# FEE SERIALIZER
# -------------------------
class FeeSerializer(serializers.ModelSerializer):
    payments = SimplePaymentSerializer(many=True, read_only=True)
    student = SimpleStudentSerializer(read_only=True)

    amount_paid = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    # for POST
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), write_only=True, source='student'
    )

    class Meta:
        model = Fee
        fields = [
            'id',
            'student',
            'total_amount',
            'term',
            'session',
            'payments',
            'amount_paid',
            'balance',
            'status',

            # write-only
            'student_id',
        ]

    def get_amount_paid(self, obj):
        return obj.amount_paid()

    def get_balance(self, obj):
        return obj.balance()

    def get_status(self, obj):
        return obj.status

class MpesaTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = MpesaTransaction

        fields = [
            'id',
            'payment',
            'phone_number',
            'checkout_request_id',
            'merchant_request_id',
            'mpesa_receipt_number',
            'amount',
            'status',
            'result_code',
            'result_description',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'checkout_request_id',
            'merchant_request_id',
            'mpesa_receipt_number',
            'status',
            'result_code',
            'result_description',
            'created_at',
            'updated_at',
        ]        