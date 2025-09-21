from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request
import logging
import json
import os
import threading

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные (замените на свои)
TOKEN = os.environ.get('TOKEN', '7806385439:AAHgwH1Wc2T2W6CfMSFrq-p9MyqV1Bsky1g')  # Используйте env-переменные для безопасности
CHANNEL_ID = os.environ.get('CHANNEL_ID', '@trusy_garderoba')
PDF_FILE_PATH = "kapsula_baza.pdf"
CHANNEL_URL = os.environ.get('CHANNEL_URL', 'https://t.me/trusy_garderoba')
IMAGE_PATH = "kapsula.png"
STATS_FILE = "stats.json"
ADMIN_ID = int(os.environ.get('ADMIN_ID', '1932002815'))  # Ваш ID

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {"guide_download_count": 0}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "👋🏻 Привет!\n"
        "Я бот канала «Трусы из моего Гардероба». Сейчас помогу тебе забрать гид «10 вещей = 28 образов».\n"
        "В этом гайде:\n"
        "✔️ список базовых вещей с ссылками на магазины\n"
        "✔️ капсульный гардероб из 10 предметов\n"
        "✔️ 28 готовых сочетаний на все случаи жизни\n"
        "🔔 Для получения файла подпишись на канал и нажми кнопку «Проверить подписку»."
    )
    
    keyboard = [
        [InlineKeyboardButton("Проверить подписку", callback_data="check_subscription")],
        [InlineKeyboardButton("Подписаться", url=CHANNEL_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        with open(IMAGE_PATH, "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=welcome_message, reply_markup=reply_markup)
    except FileNotFoundError:
        logger.error(f"Файл {IMAGE_PATH} не найден")
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
        await update.message.reply_text("Извини, не удалось загрузить изображение. Но ты всё ещё можешь получить гид!")

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    try:
        chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        
        if chat_member.status in ["member", "administrator", "creator"]:
            with open(PDF_FILE_PATH, "rb") as file:
                await query.message.reply_document(document=file, caption="Вот твой гид «10 вещей = 28 образов»! 🎉")
            
            stats = load_stats()
            stats["guide_download_count"] += 1
            save_stats(stats)
            
            await query.answer("Файл отправлен!")
        else:
            keyboard = [
                [InlineKeyboardButton("Проверить подписку", callback_data="check_subscription")],
                [InlineKeyboardButton("Подписаться", url=CHANNEL_URL)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("Похоже, ты не подписан на канал. Подпишись и попробуй снова! 🔔", reply_markup=reply_markup)
            await query.answer("Подпишись на канал!")
            
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        await query.message.reply_text("Произошла ошибка. Попробуй позже.")
        await query.answer("Ошибка!")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Эта команда доступна только администратору.")
        return
    
    stats = load_stats()
    count = stats.get("guide_download_count", 0)
    await update.message.reply_text(f"Гид «10 вещей = 28 образов» скачали: {count} раз")

# Регистрация обработчиков
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stats", stats))
application.add_handler(CallbackQueryHandler(check_subscription, pattern="check_subscription"))

# Flask для webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)
    return 'OK'

@app.route('/')
def index():
    return "Bot is running!"

if __name__ == "__main__":
    # Для Render: приложение запускается как Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)