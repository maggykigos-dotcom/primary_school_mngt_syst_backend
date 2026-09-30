from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Conversation, Message, Notification

User = get_user_model()


# =========================================================
# USER
# =========================================================

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "role",
        ]


# =========================================================
# MESSAGE
# =========================================================

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    read_by = UserSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "body",
            "attachment",
            "created_at",
            "updated_at",
            "read_by",
        ]
        read_only_fields = [
            "sender",
            "created_at",
            "updated_at",
            "read_by",
        ]


# =========================================================
# CONVERSATION
# =========================================================

class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(
        many=True,
        read_only=True
    )

    messages = MessageSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Conversation
        fields = [
            "id",
            "subject",
            "created_by",
            "participants",
            "messages",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_by",
            "participants",
            "messages",
            "created_at",
            "updated_at",
        ]


# =========================================================
# CREATE CONVERSATION
# =========================================================

class CreateConversationSerializer(serializers.Serializer):
    subject = serializers.CharField(
        max_length=255
    )

    receiver_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )

    def validate_receiver_ids(self, receiver_ids):
        receiver_ids = list(set(receiver_ids))

        existing_ids = set(
            User.objects.filter(
                id__in=receiver_ids
            ).values_list(
                "id",
                flat=True
            )
        )

        missing_ids = set(receiver_ids) - existing_ids

        if missing_ids:
            raise serializers.ValidationError(
                f"User(s) with ID(s) "
                f"{sorted(missing_ids)} do not exist."
            )

        return receiver_ids


# =========================================================
# SEND MESSAGE
# =========================================================

class SendMessageSerializer(serializers.Serializer):
    conversation_id = serializers.IntegerField()
    body = serializers.CharField()

    attachment = serializers.FileField(
        required=False,
        allow_null=True
    )


# =========================================================
# NOTIFICATION
# =========================================================

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"



# from rest_framework import serializers
# from django.contrib.auth import get_user_model
# from .models import Conversation, Message, Notification

# User = get_user_model()


# # --------------------
# # USER (LIGHT VERSION)
# # --------------------
# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ["id", "username", "role"]


# # --------------------
# # MESSAGE SERIALIZER
# # --------------------
# class MessageSerializer(serializers.ModelSerializer):
#     sender = UserSerializer(read_only=True)
#     read_by = UserSerializer(many=True, read_only=True)

#     class Meta:
#         model = Message
#         fields = [
#             "id",
#             "conversation",
#             "sender",
#             "body",
#             "attachment",
#             "created_at",
#             "updated_at",
#             "read_by",
#         ]
#         read_only_fields = ["sender"]


# # --------------------
# # CONVERSATION SERIALIZER
# # --------------------
# class ConversationSerializer(serializers.ModelSerializer):
#     participants = UserSerializer(many=True, read_only=True)
#     messages = MessageSerializer(many=True, read_only=True)

#     class Meta:
#         model = Conversation
#         fields = [
#             "id",
#             "subject",
#             "created_by",
#             "participants",
#             "messages",
#             "created_at",
#             "updated_at",
#         ]
#         read_only_fields = ["created_by"]


# # --------------------
# # CREATE CONVERSATION
# # --------------------

# class CreateConversationSerializer(serializers.Serializer):
#     subject = serializers.CharField()
#     receiver_ids = serializers.ListField(
#         child=serializers.IntegerField()
#     )

#     def validate_receiver_ids(self, receiver_ids):
#         existing_ids = set(
#             User.objects.filter(id__in=receiver_ids)
#             .values_list('id', flat=True)
#         )

#         missing_ids = set(receiver_ids) - existing_ids

#         if missing_ids:
#             raise serializers.ValidationError(
#                 f"User(s) with ID(s) {sorted(missing_ids)} do not exist."
#             )

#         return receiver_ids
  


# # --------------------
# # SEND MESSAGE
# # --------------------
# class SendMessageSerializer(serializers.Serializer):
#     conversation_id = serializers.IntegerField()
#     body = serializers.CharField()
#     attachment = serializers.FileField(required=False)


# # --------------------
# # NOTIFICATION SERIALIZER
# # --------------------
# class NotificationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Notification
#         fields = "__all__"       