import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'global_chat'
        
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        messages = await self.get_recent_messages()
        await self.send(text_data=json.dumps({
            'type': 'message_history',
            'messages': messages
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'chat_message')
        
        if message_type == 'chat_message':
            message = data['message']
            user = self.scope['user']
            
            saved_message = await self.save_message(user, message)
            
            username = await self.get_username(user)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': username,
                    'user_id': user.id,
                    'timestamp': saved_message['timestamp'],
                    'message_id': saved_message['id']
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'username': event['username'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))

    @database_sync_to_async
    def save_message(self, user, content):
        msg = Message.objects.create(user=user, content=content)
        return {
            'id': msg.id,
            'timestamp': msg.timestamp.isoformat()
        }

    @database_sync_to_async
    def get_username(self, user):
        if hasattr(user, 'nickname') and user.nickname:
            return user.nickname
        if hasattr(user, 'email') and user.email:
            return user.email.split('@')[0]
        return f"User {user.id}"

    @database_sync_to_async
    def get_recent_messages(self, limit=50):
        messages = Message.objects.select_related('user').order_by('-timestamp')[:limit]
        result = []
        for msg in reversed(messages):
            if hasattr(msg.user, 'nickname') and msg.user.nickname:
                username = msg.user.nickname
            elif hasattr(msg.user, 'email') and msg.user.email:
                username = msg.user.email.split('@')[0]
            else:
                username = f"User {msg.user.id}"
            
            result.append({
                'id': msg.id,
                'username': username,
                'user_id': msg.user.id,
                'message': msg.get_decrypted_content(),
                'timestamp': msg.timestamp.isoformat()
            })
        return result
