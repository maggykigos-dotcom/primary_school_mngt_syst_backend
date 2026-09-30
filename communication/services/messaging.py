from django.db import transaction
from django.utils.timezone import now
from communication.models import Conversation, Message, Notification
from .permissions import PermissionService


class MessagingService:

    @staticmethod
    @transaction.atomic
    def create_conversation(sender, receivers, subject):

        for r in receivers:
            if not PermissionService.can_message(sender, r):
                raise ValueError(f"{sender.role} cannot message {r.role}")

        convo = Conversation.objects.create(
            subject=subject,
            created_by=sender
        )

        convo.participants.add(sender, *receivers)

        return convo

    @staticmethod
    def send_message(sender, conversation, body, attachment=None):

        if sender not in conversation.participants.all():
            raise PermissionError("You are not part of this conversation")

        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            body=body,
            attachment=attachment
        )

        # Notify other participants
        for user in conversation.participants.exclude(id=sender.id):
            Notification.objects.create(
                user=user,
                title="New Message",
                message=body[:100]
            )

        return message