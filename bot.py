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

# In-memory task store
user_tasks = {}

# Telegram command: /addtask @username task...
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

# Telegram command: /mytask
async def my_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = '@' + user.username if user.username else None

    if not username:
        await update.message.reply_text("❗ You don’t have a username set. Please set it in Telegram settings.")
        return

    tasks = user_tasks.get(username.lower(), [])
    if not tasks:
        await update.message.reply_text("📭 You have no tasks assigned.")
        return

    task_list = '\n'.join(tasks)
    await update.message.reply_text(f"📝 Your tasks:\n\n{task_list}")

# Aiohttp webhook handler (no token check)
async def handle_webhook(request):
    data = await request.json()
    update = Update.de_json(data, app.bot)
    await app.update_queue.put(update)
    return web.Response(text="OK")

# Main async startup
async def main():
    global app
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add Telegram command handlers
    app.add_handler(CommandHandler("addtask", add_task))
    app.add_handler(CommandHandler("mytask", my_task))

    # Set Telegram webhook
    webhook_url = f"{APP_URL}/webhook/{BOT_TOKEN}"
    await app.bot.set_webhook(webhook_url)

    # Start aiohttp server
    server = web.Application()
    server.router.add_post(f"/webhook/{BOT_TOKEN}", handle_webhook)

    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print(f"🤖 Bot is running on port {PORT} via webhook.")
    await asyncio.Future()  # keep running

if __name__ == "__main__":
    asyncio.run(main())
