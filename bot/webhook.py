from aiohttp import web
from telegram import Update
from config.settings import BOT_TOKEN
from main import app  # use 'main.app' only if circular imports are handled safely

async def handle_webhook(request):
    try:
        # Extract token from URL path
        token_from_url = request.match_info.get('token')
        
        # Validate token
        if token_from_url != BOT_TOKEN:
            print(f"Invalid token in webhook URL: {token_from_url}")
            return web.Response(status=403, text="Forbidden")
        
        data = await request.json()
        print("Received update:", data)
        
        # Create update object and process it
        update = Update.de_json(data, app.bot)
        await app.update_queue.put(update)
        
        return web.Response(text="OK")
    except Exception as e:
        print("Error in webhook:", e)
        return web.Response(status=500, text="Error")
