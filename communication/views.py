from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.generics import ListAPIView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .models import Conversation, Message, Notification
from .serializers import (
    ConversationSerializer,
    MessageSerializer,
    NotificationSerializer,
    CreateConversationSerializer,
    SendMessageSerializer,
    UserSerializer,
)
from .services.messaging import MessagingService

User = get_user_model()


# =========================================================
# GET USERS THE CURRENT USER CAN MESSAGE
# =========================================================

class MessageableUsersView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Admin can message everyone except themselves
        if user.role == "admin":
            return User.objects.exclude(
                id=user.id
            ).order_by("first_name", "last_name", "username")

        # Teacher can message students and parents
        if user.role == "teacher":
            return User.objects.filter(
                role__in=["student", "parent"]
            ).exclude(
                id=user.id
            ).order_by("first_name", "last_name", "username")

        # Parent can message teachers
        if user.role == "parent":
            return User.objects.filter(
                role="teacher"
            ).order_by("first_name", "last_name", "username")

        # Student can message teachers
        if user.role == "student":
            return User.objects.filter(
                role="teacher"
            ).order_by("first_name", "last_name", "username")

        return User.objects.none()


# =========================================================
# CREATE CONVERSATION
# =========================================================

class CreateConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateConversationSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        receiver_ids = serializer.validated_data["receiver_ids"]
        subject = serializer.validated_data["subject"]

        receivers = list(
            User.objects.filter(
                id__in=receiver_ids
            )
        )

        # Make sure all requested users still exist
        if len(receivers) != len(set(receiver_ids)):
            found_ids = {user.id for user in receivers}
            missing_ids = set(receiver_ids) - found_ids

            return Response(
                {
                    "receiver_ids": [
                        f"User ID {user_id} does not exist."
                        for user_id in sorted(missing_ids)
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Do not allow a user to add themselves as receiver
        if request.user.id in receiver_ids:
            return Response(
                {
                    "receiver_ids": [
                        "You cannot select yourself as a receiver."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            convo = MessagingService.create_conversation(
                sender=request.user,
                receivers=receivers,
                subject=subject,
            )

        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "message": "Conversation created successfully.",
                "conversation_id": convo.id,
            },
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# SEND MESSAGE
# =========================================================

class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendMessageSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        convo_id = serializer.validated_data["conversation_id"]
        body = serializer.validated_data["body"]
        attachment = serializer.validated_data.get("attachment")

        conversation = get_object_or_404(
            Conversation,
            id=convo_id
        )

        # SECURITY CHECK
        if not conversation.participants.filter(
            id=request.user.id
        ).exists():
            return Response(
                {
                    "detail": "You are not part of this conversation."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            msg = MessagingService.send_message(
                sender=request.user,
                conversation=conversation,
                body=body,
                attachment=attachment,
            )

        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "message": "Message sent successfully.",
                "message_id": msg.id,
            },
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# GET USER CONVERSATIONS
# =========================================================

class UserConversationsView(ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Conversation.objects
            .filter(participants=self.request.user)
            .prefetch_related(
                "participants",
                "messages",
            )
        )


# =========================================================
# GET MESSAGES IN A CONVERSATION
# =========================================================

class ConversationMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, convo_id):
        conversation = get_object_or_404(
            Conversation,
            id=convo_id
        )

        # SECURITY CHECK
        if not conversation.participants.filter(
            id=request.user.id
        ).exists():
            return Response(
                {
                    "detail": "You are not allowed to view this conversation."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        messages = conversation.messages.all().order_by(
            "created_at"
        )

        serializer = MessageSerializer(
            messages,
            many=True
        )

        return Response(serializer.data)


# =========================================================
# MARK MESSAGE AS READ
# =========================================================

class MarkAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message_id = request.data.get("message_id")

        message = get_object_or_404(
            Message,
            id=message_id
        )

        if not message.conversation.participants.filter(
            id=request.user.id
        ).exists():
            return Response(
                {
                    "detail": "You are not part of this conversation."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        message.read_by.add(request.user)

        return Response(
            {"message": "Marked as read"}
        )


# =========================================================
# USER NOTIFICATIONS
# =========================================================

class NotificationListView(ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by("-created_at")


# =========================================================
# MARK NOTIFICATION AS READ
# =========================================================

class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        notif_id = request.data.get("notification_id")

        notif = get_object_or_404(
            Notification,
            id=notif_id,
            user=request.user
        )

        notif.is_read = True
        notif.save()

        return Response(
            {"message": "Notification marked as read"}
        )


# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework import status
# from rest_framework.generics import ListAPIView

# from django.contrib.auth import get_user_model
# from django.shortcuts import get_object_or_404

# from .models import Conversation, Message, Notification
# from .serializers import (
#     ConversationSerializer,
#     MessageSerializer,
#     NotificationSerializer,
#     CreateConversationSerializer,
#     SendMessageSerializer
# )

# from .services.messaging import MessagingService

# User = get_user_model()


# # --------------------
# # CREATE CONVERSATION
# # --------------------
# class CreateConversationView(APIView):
    
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = CreateConversationSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         receiver_ids = serializer.validated_data["receiver_ids"]
#         subject = serializer.validated_data["subject"]

#         receivers = User.objects.filter(id__in=receiver_ids)

#         convo = MessagingService.create_conversation(
#             sender=request.user,
#             receivers=list(receivers),
#             subject=subject
#         )

#         return Response({
#             "message": "Conversation created",
#             "conversation_id": convo.id
#         }, status=status.HTTP_201_CREATED)


# # --------------------
# # SEND MESSAGE
# # --------------------
# class SendMessageView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = SendMessageSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         convo_id = serializer.validated_data["conversation_id"]
#         body = serializer.validated_data["body"]
#         attachment = serializer.validated_data.get("attachment")

#         conversation = get_object_or_404(Conversation, id=convo_id)

#         msg = MessagingService.send_message(
#             sender=request.user,
#             conversation=conversation,
#             body=body,
#             attachment=attachment
#         )

#         return Response({
#             "message": "Message sent",
#             "message_id": msg.id
#         }, status=status.HTTP_201_CREATED)


# # --------------------
# # GET USER CONVERSATIONS
# # --------------------
# class UserConversationsView(ListAPIView):
#     serializer_class = ConversationSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return Conversation.objects.filter(
#             participants=self.request.user
#         ).prefetch_related("participants", "messages")


# # --------------------
# # GET MESSAGES IN A CONVERSATION
# # --------------------
# class ConversationMessagesView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, convo_id):
#         conversation = get_object_or_404(Conversation, id=convo_id)

#         # SECURITY CHECK
#         if request.user not in conversation.participants.all():
#             return Response(
#                 {"error": "Not allowed"},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         messages = conversation.messages.all().order_by("created_at")
#         serializer = MessageSerializer(messages, many=True)

#         return Response(serializer.data)


# # --------------------
# # MARK MESSAGE AS READ
# # --------------------
# class MarkAsReadView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         message_id = request.data.get("message_id")

#         message = get_object_or_404(Message, id=message_id)

#         # SECURITY CHECK
#         if request.user not in message.conversation.participants.all():
#             return Response(
#                 {"error": "You are not part of this conversation."},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         message.read_by.add(request.user)

#         return Response({"message": "Marked as read"})


# # --------------------
# # USER NOTIFICATIONS
# # --------------------
# class NotificationListView(ListAPIView):
#     serializer_class = NotificationSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return Notification.objects.filter(
#             user=self.request.user
#         ).order_by("-created_at")


# # --------------------
# # MARK NOTIFICATION AS READ
# # --------------------

# class MarkNotificationReadView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         notif_id = request.data.get("notification_id")

#         notif = get_object_or_404(Notification, id=notif_id, user=request.user)

#         # SECURITY CHECK
#         if notif.user != request.user:
#             return Response(
#                 {"error": "You cannot modify this notification."},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         notif.is_read = True
#         notif.save()

#         return Response({"message": "Notification marked as read"})
       

   
