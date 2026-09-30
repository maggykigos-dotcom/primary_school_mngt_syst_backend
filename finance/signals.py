from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payment

@receiver(post_save, sender=Payment)
def payment_post_save(sender, instance, created, **kwargs):
    if created:
        if instance.status == "successful":
            print(f" Payment successful for {instance.student} - {instance.amount}")
            

        elif instance.status == "failed":
            print(f" Payment failed for {instance.student}")

        elif instance.status == "pending":
            print(f" Payment pending for {instance.student}")
