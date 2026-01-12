"""Telegram bot for user account linking."""

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import settings
from database import AsyncSessionLocal
from clients import get_redis_client


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "Welcome to First Notifications Bot!\n\n"
            "To receive job notifications, please connect your account:\n"
            "1. Go to our website: [Click here](https://first.alshabili.site)\n"
            "2. Click *Connect Telegram* in your profile\n"
            "3. Click the link that appears",
            parse_mode="Markdown"
        )
        return

    token = args[0]
    user_telegram_id = update.effective_chat.id
    
    redis_key = f"tg_link:{token}"
    
    try:
        r = await get_redis_client()
        user_id_raw = await r.get(redis_key)
        
        if not user_id_raw:
            await update.message.reply_text(
                "Token expired or invalid.\n\n"
                "Please go back to the website and click 'Connect Telegram' again."
            )
            return

        user_id = int(user_id_raw)

        # Import here to avoid circular imports
        from api.routers.users.crud import update_telegram_id
        
        async with AsyncSessionLocal() as db:
            await update_telegram_id(db, user_id, user_telegram_id)
            
        await r.delete(redis_key)
        
        await update.message.reply_text(
            "Success! Your account is now connected.\n\n"
            "You will receive notifications for your subscribed categories."
        )
        
    except Exception as e:
        print(f"Error linking user: {e}")
        await update.message.reply_text(
            "An error occurred while linking your account.\n"
            "Please try again or contact support."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*First Notifications Bot*\n\n"
        "This bot sends you notifications about new jobs in your subscribed categories.\n\n"
        "*Commands:*\n"
        "/start - Connect your account\n"
        "/help - Show this message\n"
        "/status - Check connection status\n\n"
        "Manage your subscriptions at: https://first.alshabili.site",
        parse_mode="Markdown"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from api.routers.users.crud import get_user_by_telegram
    
    user_telegram_id = update.effective_chat.id
    
    async with AsyncSessionLocal() as db:
        user = await get_user_by_telegram(db, user_telegram_id)
        
        if user:
            await update.message.reply_text(
                f"Connected as: {user.email}\n"
                f"Max subscriptions: {user.max_categories}"
            )
        else:
            await update.message.reply_text(
                "Not connected.\n\n"
                "Connect your account via the website."
            )


def main():
    application = Application.builder().token(settings.TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    
    print(f"Starting Telegram bot: @{settings.TELEGRAM_BOT_USERNAME}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
