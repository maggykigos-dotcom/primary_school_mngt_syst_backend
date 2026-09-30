from django.urls import path
from .views import (
    MessageableUsersView,
    CreateConversationView,
    SendMessageView,
    UserConversationsView,
    ConversationMessagesView,
    MarkAsReadView,
    NotificationListView,
    MarkNotificationReadView,
)


urlpatterns = [
    # Users the current user is allowed to message
    path("users/", MessageableUsersView.as_view()),

    # Conversations
    path("conversations/", UserConversationsView.as_view()),
    path("conversations/create/", CreateConversationView.as_view()),
    path(
        "conversations/<int:convo_id>/messages/",
        ConversationMessagesView.as_view(),
    ),

    # Messages
    path("messages/send/", SendMessageView.as_view()),
    path("messages/read/", MarkAsReadView.as_view()),

    # Notifications
    path("notifications/", NotificationListView.as_view()),
    path("notifications/read/", MarkNotificationReadView.as_view()),
]



# from django.urls import path
# from .views import *

# urlpatterns = [
#     path("conversations/create/", CreateConversationView.as_view()),
#     path("messages/send/", SendMessageView.as_view()),
#     path("conversations/", UserConversationsView.as_view()),
#     path("conversations/<int:convo_id>/messages/", ConversationMessagesView.as_view()),
#     path("messages/read/", MarkAsReadView.as_view()),
#     path("notifications/", NotificationListView.as_view()),
#     path("notifications/read/", MarkNotificationReadView.as_view()),
# ]