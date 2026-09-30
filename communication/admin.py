from django.contrib import admin
from .models import Conversation, Message, Notification


# --------------------
# MESSAGE INLINE (inside conversation)
# --------------------
class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("sender", "body", "created_at")
    can_delete = False


# --------------------
# CONVERSATION ADMIN
# --------------------
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "created_by", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("subject", "created_by__username")

    filter_horizontal = ("participants",)

    inlines = [MessageInline]

    readonly_fields = ("created_at", "updated_at")


# --------------------
# MESSAGE ADMIN
# --------------------
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "short_body", "created_at")
    list_filter = ("created_at",)
    search_fields = ("body", "sender__username")

    readonly_fields = ("created_at", "updated_at")

    def short_body(self, obj):
        return obj.body[:50]
    short_body.short_description = "Message"


# --------------------
# NOTIFICATION ADMIN
# --------------------
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("title", "message", "user__username")

    readonly_fields = ("created_at", "updated_at")
