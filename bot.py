from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN= os.getenv("BOT_TOKEN")

# Tasks store: {user_id: [task1, task2, ...]}
user_tasks = {}

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # if update.effective_chat.type not in ['group', 'supergroup']:
    #     await update.message.reply_text("This command only works in groups.")
    #     return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addtask @username Task description")
        return

    # Extract username and task
    username = context.args[0]
    task_text = ' '.join(context.args[1:])

    if not username.startswith('@'):
        await update.message.reply_text("❗ Please specify the user with @username")
        return

    # For demo, just store task by username string:
    user_tasks.setdefault(username.lower(), []).append(task_text)

    await update.message.reply_text(f"Task assigned to {username}.")

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

    task_list = '\n'.join([f"{task}" for task in tasks])
    await update.message.reply_text(f"📝 Your tasks:\n\n{task_list}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("addtask", add_task))
app.add_handler(CommandHandler("mytask", my_task))

print("🤖 Bot is running... Waiting for commands.")
app.run_polling()
