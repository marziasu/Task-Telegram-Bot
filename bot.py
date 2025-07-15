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
        await update.message.reply_text("❗ You don’t have a username set. Please set it in Telegram settings.")
        return

    tasks = user_tasks.get(username.lower(), [])
    if not tasks:
        await update.message.reply_text("📭 You have no tasks assigned.")
        return

    task_list = '\n'.join(tasks)
    await update.message.reply_text(f"📝 Your tasks:\n\n{task_list}")

# 🛠️ Webhook Handler with logging and error catching
async def handle_webhook(request):
    try:
        data = await request.json()
        print("✅ Received update:", data)  # Add logging
        update = Update.de_json(data, app.bot)
        await app.update_queue.put(update)
        return web.Response(text="OK")
    except Exception as e:
        print("Error in webhook handler:", str(e))
        return web.Response(status=500, text="Internal Server Error")

async def main():
    global app
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("addtask", add_task))
    app.add_handler(CommandHandler("mytask", my_task))

    webhook_url = f"{APP_URL}/webhook/{BOT_TOKEN}"
    await app.bot.set_webhook(webhook_url)

    server = web.Application()
    server.router.add_post(f"/webhook/{BOT_TOKEN}", handle_webhook)

    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print(f"🤖 Bot running on port {PORT} via webhook at {webhook_url}")
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
