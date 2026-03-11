import os
import logging
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

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    # Initialize DB
    if not os.path.exists(database.DB_NAME):
        database.init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Checkout Conversation
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

    # Admin Add Category Conversation
    add_cat_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{texts.BTN_ADD_CATEGORY}$"), admin_handlers.add_category_start)],
        states={
            states.WAITING_CATEGORY_NAME: [MessageHandler(filters.TEXT & (~filters.COMMAND), admin_handlers.add_category_name)]
        },
        fallbacks=[MessageHandler(filters.Regex(f"^{texts.BTN_MAIN_MENU}$"), admin_handlers.cancel_admin)]
    )

    # Admin Add Product Conversation
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

    # Handlers Registration
    app.add_handler(CommandHandler("start", user_handlers.start))
    
    # Add Conversations
    app.add_handler(checkout_conv)
    app.add_handler(add_cat_conv)
    app.add_handler(add_prod_conv)

    # Admin commands outside of conv
    app.add_handler(MessageHandler(filters.Regex(f"^{texts.BTN_ADMIN}$"), admin_handlers.admin_panel))
    app.add_handler(MessageHandler(filters.Regex(f"^{texts.BTN_DELETE_PRODUCT}$"), admin_handlers.delete_product_start))
    app.add_handler(CallbackQueryHandler(admin_handlers.delete_product_callback, pattern="^delprod_"))
    app.add_handler(MessageHandler(filters.Regex(f"^{texts.BTN_ALL_ORDERS}$"), admin_handlers.view_all_orders))

    # General callback queries
    app.add_handler(CallbackQueryHandler(user_handlers.handle_callback))

    # General messages
    app.add_handler(MessageHandler(filters.PHOTO, user_handlers.handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, user_handlers.handle_document))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), user_handlers.handle_message))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
