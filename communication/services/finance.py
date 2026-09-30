from django.contrib.auth import get_user_model
from .messaging import MessagingService

User = get_user_model()


def get_system_user():
    return User.objects.get(username="system")


class FinanceService:

    @staticmethod
    def process_payment(parent, student, amount):

        # TODO: integrate with your actual payment model
        balance = 0  # Replace with real calculation

        system = get_system_user()

        convo = MessagingService.create_conversation(
            sender=system,
            receivers=[parent],
            subject="Payment Confirmation"
        )

        MessagingService.send_message(
            sender=system,
            conversation=convo,
            body=f"Payment of {amount} received. Remaining balance: {balance}"
        )
