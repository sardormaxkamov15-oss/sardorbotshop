import os
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import database
import texts
import keyboards
import states
from config import ADMIN_IDS

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(texts.ADMIN_MENU, reply_markup=keyboards.get_admin_menu_keyboard())

# --- Add Category ---
async def add_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await update.message.reply_text(texts.ASK_CATEGORY_NAME, reply_markup=keyboards.get_cancel_keyboard())
    return states.WAITING_CATEGORY_NAME

async def add_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == texts.BTN_MAIN_MENU:
        return await cancel_admin(update, context)
        
    name = update.message.text
    database.add_category(name)
    await update.message.reply_text(texts.CATEGORY_ADDED, reply_markup=keyboards.get_admin_menu_keyboard())
    return ConversationHandler.END

# --- Add Product ---
async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await update.message.reply_text(texts.ASK_PROD_CATEGORY, reply_markup=keyboards.get_categories_inline_keyboard(prefix="admincat"))
    return states.WAITING_PROD_CATEGORY

async def add_product_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "main_menu":
        await query.message.reply_text(texts.CANCEL_ADMIN, reply_markup=keyboards.get_admin_menu_keyboard())
        return ConversationHandler.END
        
    cat_id = int(query.data.split("_")[1])
    context.user_data['prod_cat_id'] = cat_id
    await query.message.reply_text(texts.ASK_PROD_NAME, reply_markup=keyboards.get_cancel_keyboard())
    return states.WAITING_PROD_NAME

async def add_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == texts.BTN_MAIN_MENU:
        return await cancel_admin(update, context)
    context.user_data['prod_name'] = update.message.text
    await update.message.reply_text(texts.ASK_PROD_IMAGE, reply_markup=keyboards.get_cancel_keyboard())
    return states.WAITING_PROD_IMAGE

async def add_product_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == texts.BTN_MAIN_MENU:
        return await cancel_admin(update, context)
        
    if update.message.photo:
        context.user_data['prod_image'] = update.message.photo[-1].file_id # Get largest
    else:
        # Assuming no photo if text
        context.user_data['prod_image'] = None
        
    await update.message.reply_text(texts.ASK_PROD_PRICE, reply_markup=keyboards.get_cancel_keyboard())
    return states.WAITING_PROD_PRICE

async def add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == texts.BTN_MAIN_MENU:
        return await cancel_admin(update, context)
    try:
        price = float(update.message.text)
        context.user_data['prod_price'] = price
        await update.message.reply_text(texts.ASK_PROD_DESC, reply_markup=keyboards.get_cancel_keyboard())
        return states.WAITING_PROD_DESC
    except ValueError:
        await update.message.reply_text(texts.ASK_PROD_PRICE)
        return states.WAITING_PROD_PRICE

async def add_product_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == texts.BTN_MAIN_MENU:
        return await cancel_admin(update, context)
    context.user_data['prod_desc'] = update.message.text
    await update.message.reply_text(texts.ASK_PROD_QTY, reply_markup=keyboards.get_cancel_keyboard())
    return states.WAITING_PROD_QTY

async def add_product_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == texts.BTN_MAIN_MENU:
        return await cancel_admin(update, context)
    try:
        qty = int(update.message.text)
        
        # Save product
        database.add_product(
            context.user_data['prod_cat_id'],
            context.user_data['prod_name'],
            context.user_data.get('prod_image'),
            context.user_data['prod_price'],
            context.user_data['prod_desc'],
            qty
        )
        
        await update.message.reply_text(texts.PRODUCT_ADDED, reply_markup=keyboards.get_admin_menu_keyboard())
        context.user_data.clear()
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(texts.ASK_PROD_QTY)
        return states.WAITING_PROD_QTY

# --- Delete Product ---
async def delete_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("O'chirish uchun mahsulotni tanlang:", reply_markup=keyboards.get_product_delete_keyboard())

async def delete_product_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(update.effective_user.id):
        return
        
    prod_id = int(query.data.split("_")[1])
    database.delete_product(prod_id)
    await query.edit_message_text(texts.PRODUCT_DELETED)

# --- View Orders ---
async def view_all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    orders = database.get_orders()
    if not orders:
        await update.message.reply_text("Hozircha buyurtmalar yo'q.")
        return
        
    # Send recent 10 orders
    for order in orders[:10]:
        msg = f"Buyurtma #{order['id']}\n"
        msg += f"Mijoz: {order['contact_name']}\n"
        msg += f"Telefon: {order['contact_phone']}\n"
        msg += f"Manzil: {order['delivery_address']}\n"
        msg += f"Jami: ${order['total_price']}\n"
        msg += f"To'lov: {order['payment_method']}\n"
        msg += f"Sana: {order['created_at']}\n"
        await update.message.reply_text(msg)

async def cancel_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(texts.CANCEL_ADMIN, reply_markup=keyboards.get_admin_menu_keyboard())
    context.user_data.clear()
    return ConversationHandler.END
