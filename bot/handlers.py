import os
import asyncio
from dotenv import load_dotenv
from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime
import json
from bot.task_db import user_tasks

task_counter = 0  # Global counter for task IDs

# Task status constants
TASK_STATUS = {
    'PENDING': '⏳ Pending',
    'IN_PROGRESS': '🔄 In Progress',
    'COMPLETED': '✅ Completed',
    'CANCELLED': '❌ Cancelled'
}

def get_next_task_id():
    global task_counter
    task_counter += 1
    return task_counter

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addtask @username Task description")
        return
    
    username = context.args[0]
    task_text = ' '.join(context.args[1:])
    
    if not username.startswith('@'):
        await update.message.reply_text("❗ Please specify the user with @username")
        return
    
    # Create task object with metadata
    task = {
        'id': get_next_task_id(),
        'description': task_text,
        'status': 'PENDING',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'assigned_by': update.effective_user.username or 'Unknown'
    }
    
    user_tasks.setdefault(username.lower(), []).append(task)
    await update.message.reply_text(f"✅ Task #{task['id']} assigned to {username}.")

async def my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = '@' + user.username if user.username else None
    
    if not username:
        await update.message.reply_text("❗ You don't have a username set. Please set it in Telegram settings.")
        return
    
    tasks = user_tasks.get(username.lower(), [])
    if not tasks:
        await update.message.reply_text("📭 You have no tasks assigned.")
        return
    
    # Group tasks by status
    pending_tasks = [t for t in tasks if t['status'] == 'PENDING']
    in_progress_tasks = [t for t in tasks if t['status'] == 'IN_PROGRESS']
    completed_tasks = [t for t in tasks if t['status'] == 'COMPLETED']
    cancelled_tasks = [t for t in tasks if t['status'] == 'CANCELLED']
    
    response = "📝 Your tasks:\n\n"
    
    if pending_tasks:
        response += "⏳ PENDING:\n"
        for task in pending_tasks:
            response += f"#{task['id']}: {task['description']}\n"
        response += "\n"
    
    if in_progress_tasks:
        response += "🔄 IN PROGRESS:\n"
        for task in in_progress_tasks:
            response += f"#{task['id']}: {task['description']}\n"
        response += "\n"
    
    if completed_tasks:
        response += "✅ COMPLETED:\n"
        for task in completed_tasks:
            response += f"#{task['id']}: {task['description']}\n"
        response += "\n"
    
    if cancelled_tasks:
        response += "❌ CANCELLED:\n"
        for task in cancelled_tasks:
            response += f"#{task['id']}: {task['description']}\n"
        response += "\n"
    
    response += "\n💡 Use /updatestatus <task_id> <status> to change task status"
    response += "\n📊 Use /taskstats to see your task statistics"
    
    await update.message.reply_text(response)

async def update_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /updatestatus <task_id> <status>\n"
            "Available statuses: pending, inprogress, completed, cancelled"
        )
        return
    
    try:
        task_id = int(context.args[0])
        new_status = context.args[1].upper()
        
        # Handle alternative status names
        status_mapping = {
            'PENDING': 'PENDING',
            'INPROGRESS': 'IN_PROGRESS',
            'IN_PROGRESS': 'IN_PROGRESS',
            'PROGRESS': 'IN_PROGRESS',
            'COMPLETED': 'COMPLETED',
            'COMPLETE': 'COMPLETED',
            'DONE': 'COMPLETED',
            'CANCELLED': 'CANCELLED',
            'CANCEL': 'CANCELLED',
            'CANCELED': 'CANCELLED'
        }
        
        if new_status not in status_mapping:
            await update.message.reply_text(
                "❗ Invalid status. Use: pending, inprogress, completed, cancelled"
            )
            return
        
        new_status = status_mapping[new_status]
        
    except ValueError:
        await update.message.reply_text("❗ Task ID must be a number.")
        return
    
    user = update.effective_user
    username = '@' + user.username if user.username else None
    
    if not username:
        await update.message.reply_text("❗ You don't have a username set.")
        return
    
    tasks = user_tasks.get(username.lower(), [])
    task_found = False
    
    for task in tasks:
        if task['id'] == task_id:
            old_status = task['status']
            task['status'] = new_status
            task['updated_at'] = datetime.now().isoformat()
            task_found = True
            
            await update.message.reply_text(
                f"✅ Task #{task_id} status updated:\n"
                f"{TASK_STATUS[old_status]} → {TASK_STATUS[new_status]}\n"
                f"📝 {task['description']}"
            )
            break
    
    if not task_found:
        await update.message.reply_text(f"❗ Task #{task_id} not found in your tasks.")

async def task_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = '@' + user.username if user.username else None
    
    if not username:
        await update.message.reply_text("❗ You don't have a username set.")
        return
    
    tasks = user_tasks.get(username.lower(), [])
    if not tasks:
        await update.message.reply_text("📭 You have no tasks assigned.")
        return
    
    # Calculate statistics
    total_tasks = len(tasks)
    pending_count = len([t for t in tasks if t['status'] == 'PENDING'])
    in_progress_count = len([t for t in tasks if t['status'] == 'IN_PROGRESS'])
    completed_count = len([t for t in tasks if t['status'] == 'COMPLETED'])
    cancelled_count = len([t for t in tasks if t['status'] == 'CANCELLED'])
    
    completion_rate = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
    
    stats_message = f"""📊 Task Statistics for {username}:

📈 Total Tasks: {total_tasks}
⏳ Pending: {pending_count}
🔄 In Progress: {in_progress_count}
✅ Completed: {completed_count}
❌ Cancelled: {cancelled_count}

📊 Completion Rate: {completion_rate:.1f}%
"""
    
    await update.message.reply_text(stats_message)

async def list_all_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to list all tasks for all users"""
    if not user_tasks:
        await update.message.reply_text("📭 No tasks in the system.")
        return
    
    response = "📋 All Tasks in System:\n\n"
    
    for username, tasks in user_tasks.items():
        response += f"👤 {username.upper()}:\n"
        for task in tasks:
            status_emoji = TASK_STATUS[task['status']]
            response += f"  #{task['id']}: {status_emoji} {task['description']}\n"
        response += "\n"
    
    await update.message.reply_text(response)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 Task Management Bot Commands:

📝 Task Management:
/addtask @username Task description - Assign a task to a user
/mytasks - View your assigned tasks grouped by status
/updatestatus <task_id> <status> - Update task status
/taskstats - View your task statistics

📊 Available Statuses:
• pending - Task not started yet
• inprogress - Task is being worked on
• completed - Task is finished
• cancelled - Task was cancelled

📋 Admin Commands:
/alltasks - List all tasks for all users (admin only)
/help - Show this help message

💡 Examples:
/addtask @john Fix the login bug
/updatestatus 1 inprogress
/updatestatus 1 completed
"""
    await update.message.reply_text(help_text)
