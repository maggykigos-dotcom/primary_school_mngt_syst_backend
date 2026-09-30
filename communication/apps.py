from django.apps import AppConfig


class CommunicationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'communication'

    def ready(self):
        # Import signals if you create them later
        try:
            import communication.signals
        except ImportError:
            pass