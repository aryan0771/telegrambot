from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from src.config.settings import settings
from src.utils.logger import logger
from src.services import mirror_service
import asyncio

class MirrorClient:
    def __init__(self):
        self.client = None
        self.phone_code_hash = None
        self.phone_number = None
        self.is_running = False
        self.init_client()

    def init_client(self):
        session_str = settings.SESSION
        if session_str == "mirror_session":
            session_str = ""
            
        if settings.API_ID and settings.API_HASH:
            self.client = TelegramClient(
                StringSession(session_str),
                int(settings.API_ID),
                settings.API_HASH,
                device_model="MirrorBot",
                system_version="1.0",
                app_version="1.0"
            )
        
    async def connect(self):
        if not self.client:
            self.init_client()
        if not self.client:
            return False
            
        if not self.client.is_connected():
            await self.client.connect()
            
        return await self.client.is_user_authorized()

    async def send_code(self, phone: str):
        if not await self.connect():
            # If connect returns false, we are not authorized, but we are connected.
            # Send code request
            result = await self.client.send_code_request(phone)
            self.phone_code_hash = result.phone_code_hash
            self.phone_number = phone
            return True
        return False

    async def sign_in(self, code: str, password: str = None):
        try:
            if password:
                await self.client.sign_in(password=password)
            else:
                await self.client.sign_in(
                    phone=self.phone_number,
                    code=code,
                    phone_code_hash=self.phone_code_hash
                )
                
            session_string = self.client.session.save()
            settings.update_env("SESSION", session_string)
            return True, session_string
        except SessionPasswordNeededError:
            return False, "PASSWORD_NEEDED"
        except Exception as e:
            return False, str(e)

    async def logout(self):
        if not await self.connect():
            return False
            
        try:
            self.stop_mirroring()
            await self.client.log_out()
            settings.update_env("SESSION", "")
            self.client = None
            self.init_client()
            return True
        except Exception as e:
            logger.error(f"Error logging out: {e}")
            return False

    async def get_dialogs(self):
        if not await self.connect():
            return []
            
        channels = []
        async for dialog in self.client.iter_dialogs(limit=100):
            if dialog.is_channel or dialog.is_group:
                channels.append({
                    "id": str(dialog.id),
                    "name": dialog.name
                })
        return channels

    async def start_mirroring(self):
        if not await self.connect():
            logger.error("Cannot start mirroring: Not authorized.")
            return False
            
        try:
            settings.validate()
        except ValueError as e:
            logger.error(f"Cannot start mirroring: {e}")
            return False

        if not self.is_running:
            self.register_handlers()
            self.is_running = True
            logger.info("Mirroring started successfully.")
        return True

    def stop_mirroring(self):
        if self.client and self.is_running:
            self.client.remove_event_handler(mirror_service.handle_new_message)
            self.client.remove_event_handler(mirror_service.handle_edit_message)
            self.client.remove_event_handler(mirror_service.handle_delete_message)
            self.is_running = False
            logger.info("Mirroring stopped.")
        return True

    def register_handlers(self):
        # Remove existing handlers first to avoid duplicates
        self.stop_mirroring()
        
        # We need to ensure the ID is an integer
        source_id = int(settings.SOURCE_CHANNEL)
        
        self.client.add_event_handler(
            mirror_service.handle_new_message, 
            events.NewMessage(chats=source_id)
        )
        self.client.add_event_handler(
            mirror_service.handle_edit_message, 
            events.MessageEdited(chats=source_id)
        )
        self.client.add_event_handler(
            mirror_service.handle_delete_message, 
            events.MessageDeleted(chats=source_id)
        )
            
        logger.info(f"Registered event handlers for source channel: {source_id}")

mirror_client = MirrorClient()
