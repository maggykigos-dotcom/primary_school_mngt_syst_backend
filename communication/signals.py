# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Message


# @receiver(post_save, sender=Message, dispatch_uid="message_notification_signal")
# def notify_on_message(sender, instance, created, **kwargs):
#     if not created:
#         return

#     try:
#         from .services.messaging import MessagingService

#         MessagingService.create_notifications(instance)

#     except Exception as e:
#         # Optional: log error instead of crashing
#         print(f"Signal error (notify_on_message): {e}")