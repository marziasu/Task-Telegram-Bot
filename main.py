
import asyncio
from aiohttp import web
from telegram.ext import ApplicationBuilder, CommandHandler
from config.settings import BOT_TOKEN, APP_URL, PORT
from bot.handlers import add_task, my_tasks, update_status, task_stats, list_all_tasks, help_command
from bot.webhook import handle_webhook
from app_core import app

# Register routes
app.include_router(handle_webhook)

app = None  # Global variable to store the application

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

async def main():
    global app
    
    # Build the application
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("addtask", add_task))
    app.add_handler(CommandHandler("mytask", my_tasks))
    app.add_handler(CommandHandler("update_status", update_status))
    app.add_handler(CommandHandler("task_stats", task_stats))
    app.add_handler(CommandHandler("list_all_tasks", list_all_tasks))
    app.add_handler(CommandHandler("help_command", help_command))

    # Set webhook
    webhook_url = f"{APP_URL}/webhook/{BOT_TOKEN}"
    print(f"Setting webhook to: {webhook_url}")
    
    webhook_info = await app.bot.set_webhook(webhook_url)
    print(f"📡 Webhook set: {webhook_info}")

    # Create web server
    server = web.Application()
    server.router.add_post("/webhook/{token}", handle_webhook)
    server.router.add_get("/", health_check)  # Health check endpoint
    server.router.add_get("/health", health_check)  # Alternative health check

    # Initialize the application
    await app.initialize()
    await app.start()

    # Start the web server
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print(f"🚀 Bot is running on port {PORT}")
    print(f"📍 Webhook URL: {webhook_url}")
    print(f"🔍 Health check: {APP_URL}/health")
    
    # Keep the application running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
    finally:
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())