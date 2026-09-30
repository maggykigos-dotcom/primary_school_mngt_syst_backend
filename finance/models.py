from django.db import models
from accounts.models import Student, Parent


# 💵 SCHOOL FEE STRUCTURE
class Fee(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fees')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    term = models.CharField(max_length=50)
    session = models.CharField(max_length=50)
    def amount_paid(self):
        from django.db.models import Sum
        return self.payments.filter(status='successful').aggregate(
            total=Sum('amount')
            )['total'] or 0


    def balance(self):
        return self.total_amount - self.amount_paid()

    def __str__(self):
        return f"{self.student} - Balance: {self.balance()}"

    @property
    def status(self):
        if self.balance() == 0:
            return "paid"
        elif self.amount_paid() > 0:
            return "partial"
        return "unpaid"    


# 💳 PAYMENT METHODS
class PaymentMethod(models.Model):
    METHOD_CHOICES = (
        ('mpesa', 'M-Pesa'),
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
    )

    name = models.CharField(max_length=20, choices=METHOD_CHOICES)

    def __str__(self):
        return self.name



from django.core.exceptions import ValidationError

class Payment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='payments')
    fee = models.ForeignKey(Fee, on_delete=models.CASCADE, related_name='payments')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)

    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    

    status = models.CharField(
        max_length=20,
        choices=[
            ('pending','Pending'),
            ('successful','Successful'),
            ('failed','Failed'),
        ],
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.student not in self.parent.students.all():
            raise ValidationError("This student does not belong to this parent")

        if self.amount <= 0:
            raise ValidationError("Payment must be greater than zero")

        if self.fee.balance() < self.amount:
            raise ValidationError("Payment exceeds remaining balance")    

    def __str__(self):
        return f"{self.student} - {self.amount}"

class MpesaTransaction(models.Model):
    STATUS_CHOICES = (
        ('initiated', 'Initiated'),
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='mpesa_transaction'
    )

    phone_number = models.CharField(max_length=15)

    checkout_request_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    merchant_request_id = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    mpesa_receipt_number = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='initiated'
    )

    result_code = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    result_description = models.TextField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.payment.id} - {self.status}"