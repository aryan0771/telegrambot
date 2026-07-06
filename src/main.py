import sys
import os
import uvicorn
import asyncio

# Ensure the parent directory is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.logger import logger

def main():
    logger.info("Starting Telegram Mirror Dashboard & Server...")
    
    # Avoid NotImplementedError on Windows when using asyncio with Uvicorn
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    # Start the web server. The Telegram bot starts dynamically within the FastAPI app.
    # We use import string to let uvicorn reload work (though reload=False by default)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=port, log_level="info")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application stopped manually.")
    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
        sys.exit(1)
