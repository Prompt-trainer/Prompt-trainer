import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Conversation, Message
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "global_chat"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        messages = await self.get_recent_messages()
        await self.send(
            text_data=json.dumps({"type": "message_history", "messages": messages})
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type", "chat_message")

        if message_type == "chat_message":
            message = data["message"]
            user = self.scope["user"]

            saved_message = await self.save_message(user, message)

            username = await self.get_username(user)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "username": username,
                    "user_id": user.id,
                    "timestamp": saved_message["timestamp"],
                    "message_id": saved_message["id"],
                },
            )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "message": event["message"],
                    "username": event["username"],
                    "user_id": event["user_id"],
                    "timestamp": event["timestamp"],
                    "message_id": event["message_id"],
                }
            )
        )

    @database_sync_to_async
    def save_message(self, user, content):
        msg = Message.objects.create(user=user, content=content)
        return {"id": msg.id, "timestamp": msg.timestamp.isoformat()}

    @database_sync_to_async
    def get_username(self, user):
        if hasattr(user, "nickname") and user.nickname:
            return user.nickname
        if hasattr(user, "email") and user.email:
            return user.email.split("@")[0]
        return f"User {user.id}"

    @database_sync_to_async
    def get_recent_messages(self, limit=50):
        messages = Message.objects.select_related("user").order_by("-timestamp")[:limit]
        result = []
        for msg in reversed(messages):
            if hasattr(msg.user, "nickname") and msg.user.nickname:
                username = msg.user.nickname
            elif hasattr(msg.user, "email") and msg.user.email:
                username = msg.user.email.split("@")[0]
            else:
                username = f"User {msg.user.id}"

            result.append(
                {
                    "id": msg.id,
                    "username": username,
                    "user_id": msg.user.id,
                    "message": msg.get_decrypted_content(),
                    "timestamp": msg.timestamp.isoformat(),
                }
            )
        return result


class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.other_user_id = self.scope["url_route"]["kwargs"]["user_id"]

        if not self.user.is_authenticated:
            await self.close()
            return

        user_ids = sorted([self.user.id, int(self.other_user_id)])
        self.room_group_name = f"private_chat_{user_ids[0]}_{user_ids[1]}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        messages = await self.get_messages()
        await self.send(
            text_data=json.dumps({"type": "message_history", "messages": messages})
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type", "message")

        if message_type == "message":
            message_content = data["message"]
            message = await self.save_message(self.user, message_content)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message_content,
                    "sender": self.user.nickname,
                    "sender_id": self.user.id,
                    "timestamp": message["timestamp"],
                    "message_id": message["id"],
                },
            )

        elif message_type == "mark_read":
            await self.mark_messages_read()

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message",
                    "message": event["message"],
                    "sender": event["sender"],
                    "sender_id": event["sender_id"],
                    "timestamp": event["timestamp"],
                    "message_id": event["message_id"],
                }
            )
        )

    @database_sync_to_async
    def save_message(self, user, content):
        other_user = User.objects.get(id=self.other_user_id)
        conversation = Conversation.get_or_create_conversation(user, other_user)

        with transaction.atomic():
            msg = Message.objects.create(
                user=user, content=content, conversation=conversation
            )
            return {"id": msg.id, "timestamp": msg.timestamp.isoformat()}

    @database_sync_to_async
    def get_messages(self):
        other_user = User.objects.get(id=self.other_user_id)
        conversation = Conversation.get_or_create_conversation(self.user, other_user)
        messages = conversation.messages.select_related("user").order_by("timestamp")[
            :50
        ]

        return [
            {
                "id": msg.id,
                "message": msg.get_decrypted_content(),
                "timestamp": msg.timestamp.isoformat(),
                "sender": msg.user.nickname,
                "sender_id": msg.user.id,
                "is_read": msg.is_read,
            }
            for msg in messages
        ]

    @database_sync_to_async
    def mark_messages_read(self):
        other_user = User.objects.get(id=self.other_user_id)
        conversation = Conversation.get_or_create_conversation(self.user, other_user)

        conversation.messages.filter(user=other_user, is_read=False).update(
            is_read=True
        )
