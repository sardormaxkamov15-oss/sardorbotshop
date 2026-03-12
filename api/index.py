import os
import asyncio
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler
)
from config import BOT_TOKEN
import database
import texts
import states
from handlers import user_handlers, admin_handlers

app = FastAPI()

# Initialize Telegram Application
# We use a global variable to keep the app instance
tg_app = None

async def get_tg_app():
    global tg_app
    if tg_app is None:
        database.init_db()
            
        tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Register handlers (identical to main.py logic)
        checkout_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(user_handlers.checkout_start, pattern="^checkout$")],
            states={
                states.WAITING_NAME: [MessageHandler(filters.TEXT & (~filters.COMMAND), user_handlers.checkout_name)],
                states.WAITING_PHONE: [MessageHandler(filters.CONTACT | (filters.TEXT & (~filters.COMMAND)), user_handlers.checkout_phone)],
                states.WAITING_ADDRESS: [MessageHandler(filters.TEXT & (~filters.COMMAND), user_handlers.checkout_address)],
                states.WAITING_PAYMENT: [MessageHandler(filters.TEXT & (~filters.COMMAND), user_handlers.checkout_payment)],
            },
            fallbacks=[MessageHandler(filters.Regex(f"^{texts.BTN_MAIN_MENU}$"), user_handlers.cancel_checkout)]
        )

        add_cat_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(f"^{texts.BTN_ADD_CATEGORY}$"), admin_handlers.add_category_start)],
            states={
                states.WAITING_CATEGORY_NAME: [MessageHandler(filters.TEXT & (~filters.COMMAND), admin_handlers.add_category_name)]
            },
            fallbacks=[MessageHandler(filters.Regex(f"^{texts.BTN_MAIN_MENU}$"), admin_handlers.cancel_admin)]
        )

        add_prod_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(f"^{texts.BTN_ADD_PRODUCT}$"), admin_handlers.add_product_start)],
            states={
                states.WAITING_PROD_CATEGORY: [CallbackQueryHandler(admin_handlers.add_product_category, pattern="^(admincat_|main_menu)")],
                states.WAITING_PROD_NAME: [MessageHandler(filters.TEXT & (~filters.COMMAND), admin_handlers.add_product_name)],
                states.WAITING_PROD_IMAGE: [MessageHandler(filters.PHOTO | (filters.TEXT & (~filters.COMMAND)), admin_handlers.add_product_image)],
                states.WAITING_PROD_PRICE: [MessageHandler(filters.TEXT & (~filters.COMMAND), admin_handlers.add_product_price)],
                states.WAITING_PROD_DESC: [MessageHandler(filters.TEXT & (~filters.COMMAND), admin_handlers.add_product_desc)],
                states.WAITING_PROD_QTY: [MessageHandler(filters.TEXT & (~filters.COMMAND), admin_handlers.add_product_qty)],
            },
            fallbacks=[MessageHandler(filters.Regex(f"^{texts.BTN_MAIN_MENU}$"), admin_handlers.cancel_admin)]
        )

        tg_app.add_handler(CommandHandler("start", user_handlers.start))
        tg_app.add_handler(checkout_conv)
        tg_app.add_handler(add_cat_conv)
        tg_app.add_handler(add_prod_conv)
        tg_app.add_handler(MessageHandler(filters.Regex(f"^{texts.BTN_ADMIN}$"), admin_handlers.admin_panel))
        tg_app.add_handler(MessageHandler(filters.Regex(f"^{texts.BTN_DELETE_PRODUCT}$"), admin_handlers.delete_product_start))
        tg_app.add_handler(CallbackQueryHandler(admin_handlers.delete_product_callback, pattern="^delprod_"))
        tg_app.add_handler(MessageHandler(filters.Regex(f"^{texts.BTN_ALL_ORDERS}$"), admin_handlers.view_all_orders))
        tg_app.add_handler(CallbackQueryHandler(user_handlers.handle_callback))
        
        # Sticker Handlers
        tg_app.add_handler(MessageHandler(filters.PHOTO, user_handlers.handle_photo))
        tg_app.add_handler(MessageHandler(filters.Document.IMAGE, user_handlers.handle_document))
        
        tg_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), user_handlers.handle_message))
        
        await tg_app.initialize()
    return tg_app

@app.post("/api/webhook")
async def webhook(request: Request):
    application = await get_tg_app()
    update = Update.de_json(await request.json(), application.bot)
    await application.process_update(update)
    return {"status": "ok"}

@app.get("/")
async def index():
    return {"message": "Telegram Bot is running!"}
