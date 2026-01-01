import asyncio
import signal
import logging
from contextlib import asynccontextmanager
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.v1.upload import background_tasks_set

logger = logging.getLogger(__name__)

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"🛑 Received signal {signum}, cancelling background tasks...")
        # Cancel all background tasks
        for task in list(background_tasks_set):
            try:
                if not task.done():
                    task.cancel()
                    logger.info(f"   ✓ Task cancelled")
            except Exception as e:
                logger.warning(f"   ⚠️  Error cancelling task: {e}")
        background_tasks_set.clear()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

@asynccontextmanager
async def lifespan(app):
    # Startup
    logger.info("🔌 Connecting to MongoDB...")
    try:
        await connect_to_mongo()
        logger.info("✅ MongoDB connected")
    except Exception as e:
        logger.warning(f"⚠️  MongoDB connection failed: {e}")
        logger.warning("   Server will start but database operations may fail")
    
    # Setup signal handlers
    setup_signal_handlers()
    
    yield
    
    # Shutdown - cancel all background tasks immediately
    logger.info("🛑 Shutting down...")
    
    # Cancel all background tasks
    if background_tasks_set:
        logger.info(f"   🔪 Cancelling {len(background_tasks_set)} background task(s)...")
        for task in list(background_tasks_set):
            try:
                if not task.done():
                    task.cancel()
                    logger.info(f"   ✓ Task cancelled")
            except Exception as e:
                logger.warning(f"   ⚠️  Error cancelling task: {e}")
    
    # Clear the set
    background_tasks_set.clear()
    
    await close_mongo_connection()
    logger.info("✅ Shutdown complete")
