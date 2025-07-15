import os
import asyncio
from dotenv import load_dotenv
from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL")
PORT = int(os.getenv("PORT", "8443"))

user_tasks = {}
app = None  # Global variable to store the application

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addtask @username Task description")
        return
    username = context.args[0]
    task_text = ' '.join(context.args[1:])
    if not username.startswith('@'):
        await update.message.reply_text("❗ Please specify the user with @username")
        return
    user_tasks.setdefault(username.lower(), []).append(task_text)
    await update.message.reply_text(f"✅ Task assigned to {username}.")

async def my_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = '@' + user.username if user.username else None
    if not username:
        await update.message.reply_text("❗ You don't have a username set. Please set it in Telegram settings.")
        return
    tasks = user_tasks.get(username.lower(), [])
    if not tasks:
        await update.message.reply_text("📭 You have no tasks assigned.")
        return
    task_list = '\n'.join(tasks)
    await update.message.reply_text(f"📝 Your tasks:\n\n{task_list}")

# Webhook handler with token validation
async def handle_webhook(request):
    try:
        # Extract token from URL path
        token_from_url = request.match_info.get('token')
        
        # Validate token
        if token_from_url != BOT_TOKEN:
            print(f"❌ Invalid token in webhook URL: {token_from_url}")
            return web.Response(status=403, text="Forbidden")
        
        data = await request.json()
        print("✅ Received update:", data)
        
        # Create update object and process it
        update = Update.de_json(data, app.bot)
        await app.update_queue.put(update)
        
        return web.Response(text="OK")
    except Exception as e:
        print("❌ Error in webhook:", e)
        return web.Response(status=500, text="Error")

# Health check endpoint
async def health_check(request):
    return web.Response(text="Bot is running!")

async def main():
    global app
    
    # Build the application
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("addtask", add_task))
    app.add_handler(CommandHandler("mytask", my_task))

    # Set webhook
    webhook_url = f"{APP_URL}/webhook/{BOT_TOKEN}"
    print(f"🔗 Setting webhook to: {webhook_url}")
    
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