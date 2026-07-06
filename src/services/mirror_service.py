from telethon import events, errors
from src.config.settings import settings
from src.utils.logger import logger
from src.storage import db
import asyncio

async def handle_new_message(event):
    client = event.client
    # If the message is a service message (e.g., pinned, joined), we might want to skip it
    if event.message.action:
        return
        
    source_msg_id = event.message.id
    
    # Check if we already processed this
    if await db.is_message_processed(source_msg_id):
        logger.debug(f"Message {source_msg_id} already processed. Skipping.")
        return

    try:
        logger.info(f"New message received from source: {source_msg_id}")
        
        # We copy the message by sending its text and media directly.
        # This prevents the 'Forwarded from' tag.
        
        # Handle Albums (Grouped messages)
        # For simplicity, if it has a grouped_id, it is part of an album. 
        # Telethon doesn't easily send albums without collecting them first.
        # However, sending them individually is a safe fallback if we don't want to build a complex collector.
        # But wait, telethon's send_message can take a list of InputMedia if we want an album.
        # To keep it robust and simple with minimal latency, we will send them as they arrive.
        
        sent_msg = await client.send_message(
            settings.DESTINATION_CHANNEL,
            message=event.message.message,
            file=event.message.media,
            formatting_entities=event.message.entities,
            link_preview=bool(event.message.web_preview) if hasattr(event.message, 'web_preview') else None
        )
        
        if sent_msg:
            # Map the message IDs for future edits/deletions
            await db.map_message(source_msg_id, sent_msg.id)
            await db.mark_message_processed(source_msg_id)
            logger.info(f"Successfully mirrored message {source_msg_id} -> {sent_msg.id}")
            
    except errors.FloodWaitError as e:
        logger.warning(f"Flood wait error. Sleeping for {e.seconds} seconds.")
        await asyncio.sleep(e.seconds)
        # Retry once
        await handle_new_message(client, event)
    except Exception as e:
        logger.error(f"Error mirroring message {source_msg_id}: {e}", exc_info=True)


async def handle_edit_message(event):
    client = event.client
    source_msg_id = event.message.id
    
    dest_msg_id = await db.get_mapped_message(source_msg_id)
    if not dest_msg_id:
        logger.debug(f"Edited message {source_msg_id} has no mapped destination. Skipping.")
        return
        
    try:
        logger.info(f"Message {source_msg_id} edited. Updating destination {dest_msg_id}")
        await client.edit_message(
            entity=settings.DESTINATION_CHANNEL,
            message=dest_msg_id,
            text=event.message.message,
            file=event.message.media,
            formatting_entities=event.message.entities,
            link_preview=bool(event.message.web_preview) if hasattr(event.message, 'web_preview') else None
        )
        logger.info(f"Successfully updated message {dest_msg_id}")
    except errors.MessageNotModifiedError:
        pass
    except Exception as e:
        logger.error(f"Error editing message {dest_msg_id}: {e}", exc_info=True)


async def handle_delete_message(event):
    client = event.client
    for source_msg_id in event.deleted_ids:
        dest_msg_id = await db.get_mapped_message(source_msg_id)
        if dest_msg_id:
            try:
                logger.info(f"Message {source_msg_id} deleted. Deleting destination {dest_msg_id}")
                await client.delete_messages(settings.DESTINATION_CHANNEL, dest_msg_id)
                await db.remove_mapping(source_msg_id)
                logger.info(f"Successfully deleted message {dest_msg_id}")
            except Exception as e:
                logger.error(f"Error deleting message {dest_msg_id}: {e}", exc_info=True)
