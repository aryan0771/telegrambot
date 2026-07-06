import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from src.config.settings import settings
import sys
import os

# Ensure the parent directory is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

async def main():
    if not settings.SESSION or settings.SESSION == "mirror_session":
        print("Please set your SESSION string in .env first.")
        return
        
    client = TelegramClient(
        StringSession(settings.SESSION),
        settings.API_ID,
        settings.API_HASH
    )
    
    print("Connecting to Telegram...")
    await client.start()
    
    print("\n" + "="*50)
    print("YOUR RECENT CHANNELS AND GROUPS:")
    print("="*50)
    
    # Fetch recent dialogs
    async for dialog in client.iter_dialogs(limit=50):
        if dialog.is_channel or dialog.is_group:
            print(f"Name: {dialog.name}")
            print(f"ID:   {dialog.id}")
            print("-" * 50)
            
    print("\nCopy the correct ID (it should start with -100) and paste it into your .env file")
    print("for SOURCE_CHANNEL and DESTINATION_CHANNEL.")
    
if __name__ == "__main__":
    # Avoid NotImplementedError on Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
