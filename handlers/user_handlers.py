import os
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import database
import texts
import keyboards
import states
try:
    import sticker_utils
    STICKER_AVAILABLE = True
except ImportError:
    STICKER_AVAILABLE = False
from config import ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    database.add_user(user.id, user.full_name)
    
    is_admin = user.id in ADMIN_IDS
    await update.message.reply_text(
        texts.MAIN_MENU,
        reply_markup=keyboards.get_main_menu_keyboard(is_admin)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    is_admin = user_id in ADMIN_IDS
    
    if text == texts.BTN_PRODUCTS:
        await update.message.reply_text(texts.CATEGORIES_TEXT, reply_markup=keyboards.get_categories_inline_keyboard())
    elif text == texts.BTN_SUPPORT:
        await update.message.reply_text(texts.SUPPORT_TEXT)
    elif text == texts.BTN_SOCIALS:
        await update.message.reply_text(texts.SOCIALS_TEXT, reply_markup=keyboards.get_socials_keyboard())
    elif text == texts.BTN_CONTACT:
        await update.message.reply_text(texts.CONTACT_TEXT)
    elif text == texts.BTN_ABOUT:
        await update.message.reply_text(texts.ABOUT_TEXT)
    elif text == texts.BTN_HARID:
        await update.message.reply_text(texts.HARID_TEXT, reply_markup=keyboards.get_harid_keyboard())
    elif text == texts.BTN_MAIN_MENU:
        await update.message.reply_text(texts.MAIN_MENU, reply_markup=keyboards.get_main_menu_keyboard(is_admin))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id
    
    if data == "main_menu":
        is_admin = user_id in ADMIN_IDS
        await query.message.reply_text(texts.MAIN_MENU, reply_markup=keyboards.get_main_menu_keyboard(is_admin))
        await query.message.delete()
        
    elif data == "back_categories":
        await query.edit_message_text(texts.CATEGORIES_TEXT, reply_markup=keyboards.get_categories_inline_keyboard())
        
    elif data.startswith("cat_"):
        cat_id = int(data.split("_")[1])
        category = database.get_category(cat_id)
        msg = "Mahsulotni tanlang:"
        if category:
            price_text = texts.CATEGORY_PRICES.get(category['name'], "")
            if price_text:
                msg = f"{price_text}\n\nMahsulotni tanlang:"
        await query.edit_message_text(msg, reply_markup=keyboards.get_products_keyboard(cat_id))
        
    elif data.startswith("prod_"):
        prod_id = int(data.split("_")[1])
        product = database.get_product(prod_id)
        if not product:
            await query.edit_message_text(texts.PROD_NOT_FOUND)
            return
            
        caption = texts.PRODUCT_CAPTION.format(
            name=product['name'],
            price=product['price'],
            description=product['description'],
            quantity=product['quantity']
        )
        markup = keyboards.get_product_detail_keyboard(product['id'])
        
        if product['image_id']:
            await query.message.delete()
            await context.bot.send_photo(
                chat_id=user_id,
                photo=product['image_id'],
                caption=caption,
                reply_markup=markup
            )
        else:
            await query.edit_message_text(caption, reply_markup=markup)
            
    elif data.startswith("addcart_"):
        prod_id = int(data.split("_")[1])
        product = database.get_product(prod_id)
        if product and product['quantity'] > 0:
            database.add_to_cart(user_id, prod_id)
            await query.answer("Savatga qo'shildi!", show_alert=True)
        else:
            await query.answer("Mahsulot tugagan!", show_alert=True)
            
    elif data.startswith("rmcart_"):
        prod_id = int(data.split("_")[1])
        database.remove_from_cart(user_id, prod_id)
        await show_cart_query(query, user_id)
        
    elif data == "clearcart":
        database.clear_cart(user_id)
        await show_cart_query(query, user_id)
        
    elif data == "show_cart":
        await show_cart_query(query, user_id)

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart = database.get_cart(user_id)
    if not cart:
        await update.message.reply_text(texts.EMPTY_CART, reply_markup=keyboards.get_cart_keyboard(cart))
        return
        
    total = sum(item['total'] for item in cart)
    items_str = "\n".join([f"🔸 {it['name']} x{it['quantity']} = ${it['total']}" for it in cart])
    msg = texts.CART_INFO.format(items=items_str, total=total)
    
    await update.message.reply_text(msg, reply_markup=keyboards.get_cart_keyboard(cart))

async def show_cart_query(query, user_id):
    cart = database.get_cart(user_id)
    if not cart:
        await query.edit_message_text(texts.EMPTY_CART, reply_markup=keyboards.get_cart_keyboard(cart))
        return
        
    total = sum(item['total'] for item in cart)
    items_str = "\n".join([f"🔸 {it['name']} x{it['quantity']} = ${it['total']}" for it in cart])
    msg = texts.CART_INFO.format(items=items_str, total=total)
    
    await query.edit_message_text(msg, reply_markup=keyboards.get_cart_keyboard(cart))


# --- Checkout Conversation ---
async def checkout_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    cart = database.get_cart(user_id)
    if not cart:
        await query.message.reply_text(texts.EMPTY_CART)
        return ConversationHandler.END
        
    await query.message.reply_text(texts.ASK_NAME, reply_markup=keyboards.get_cancel_keyboard())
    return states.WAITING_NAME

async def checkout_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == texts.BTN_MAIN_MENU:
        return await cancel_checkout(update, context)
        
    context.user_data['order_name'] = update.message.text
    await update.message.reply_text(texts.ASK_PHONE, reply_markup=keyboards.get_contact_keyboard())
    return states.WAITING_PHONE

async def checkout_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == texts.BTN_MAIN_MENU:
        return await cancel_checkout(update, context)
        
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text
        
    context.user_data['order_phone'] = phone
    database.set_user_phone(update.effective_user.id, phone)
    
    await update.message.reply_text(texts.ASK_ADDRESS, reply_markup=keyboards.get_cancel_keyboard())
    return states.WAITING_ADDRESS

async def checkout_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == texts.BTN_MAIN_MENU:
        return await cancel_checkout(update, context)
        
    context.user_data['order_address'] = update.message.text
    await update.message.reply_text(texts.ASK_PAYMENT, reply_markup=keyboards.get_payment_keyboard())
    return states.WAITING_PAYMENT

async def checkout_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == texts.BTN_MAIN_MENU:
        return await cancel_checkout(update, context)
        
    payment = update.message.text
    user_id = update.effective_user.id
    cart = database.get_cart(user_id)
    if not cart:
        await update.message.reply_text(texts.EMPTY_CART, reply_markup=keyboards.get_main_menu_keyboard(user_id in ADMIN_IDS))
        return ConversationHandler.END
        
    total_price = sum(item['total'] for item in cart)
    
    order_id = database.create_order(
        user_id,
        total_price,
        payment,
        context.user_data['order_address'],
        context.user_data['order_phone'],
        context.user_data['order_name'],
        cart
    )
    
    await update.message.reply_text(texts.ORDER_SUCCESS, reply_markup=keyboards.get_main_menu_keyboard(user_id in ADMIN_IDS))
    
    # Notify Admins
    items_str = "\n".join([f"🔸 {it['name']} x{it['quantity']} = ${it['total']}" for it in cart])
    admin_msg = texts.ORDER_ADMIN_NOTIFY.format(
        order_id=order_id,
        name=context.user_data['order_name'],
        phone=context.user_data['order_phone'],
        address=context.user_data['order_address'],
        payment=payment,
        total=total_price,
        items=items_str
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_msg)
        except Exception as e:
            pass
            
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(texts.CANCEL_ADMIN, reply_markup=keyboards.get_main_menu_keyboard(user_id in ADMIN_IDS))
    context.user_data.clear()
    return ConversationHandler.END

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles photos sent by the user and converts them to stickers."""
    if not STICKER_AVAILABLE:
        await update.message.reply_text("Stiker funksiyasi hozirda mavjud emas.")
        return
    try:
        # Get the largest photo
        file_id = update.message.photo[-1].file_id
        
        processing_msg = await update.message.reply_text("Stiker tayyorlanmoqda... ⏳")
        
        # Download file
        file = await context.bot.get_file(file_id)
        file_bytes = await file.download_as_bytearray()
        
        # Process sticker
        sticker_buffer = sticker_utils.process_sticker(bytes(file_bytes))
        
        # Send sticker
        await update.message.reply_sticker(sticker=sticker_buffer)
        
        # Delete processing message
        await processing_msg.delete()
        
    except Exception as e:
        await update.message.reply_text(f"Xatolik yuz berdi: {e}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles documents sent by the user and converts them to stickers if they are images."""
    if not STICKER_AVAILABLE:
        await update.message.reply_text("Stiker funksiyasi hozirda mavjud emas.")
        return
    if not update.message.document.mime_type.startswith('image/'):
        return
        
    try:
        file_id = update.message.document.file_id
        
        processing_msg = await update.message.reply_text("Stiker tayyorlanmoqda... ⏳")
        
        # Download file
        file = await context.bot.get_file(file_id)
        file_bytes = await file.download_as_bytearray()
        
        # Process sticker
        sticker_buffer = sticker_utils.process_sticker(bytes(file_bytes))
        
        # Send sticker
        await update.message.reply_sticker(sticker=sticker_buffer)
        
        # Delete processing message
        await processing_msg.delete()
        
    except Exception as e:
        await update.message.reply_text(f"Xatolik yuz berdi: {e}")
