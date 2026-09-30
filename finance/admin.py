from django.contrib import admin

from .models import (
    Fee,
    Payment,
    PaymentMethod,
    MpesaTransaction
)


admin.site.register(Fee)

admin.site.register(Payment)

admin.site.register(PaymentMethod)

admin.site.register(MpesaTransaction)