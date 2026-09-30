from communication.models import Notification

class NotificationService:

    @staticmethod
    def notify(user, title, message):
        Notification.objects.create(
            user=user,
            title=title,
            message=message
        )
