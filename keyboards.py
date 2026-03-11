from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import database
import texts

def get_main_menu_keyboard(is_admin=False):
    keyboard = [
        [KeyboardButton(texts.BTN_PRODUCTS), KeyboardButton(texts.BTN_HARID)],
        [KeyboardButton(texts.BTN_SOCIALS), KeyboardButton(texts.BTN_CONTACT)],
        [KeyboardButton(texts.BTN_ABOUT), KeyboardButton(texts.BTN_SUPPORT)]
    ]
    if is_admin:
        # Give admins access to an admin panel
        keyboard.append([KeyboardButton(texts.BTN_ADMIN)])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_menu_keyboard():
    keyboard = [
        [KeyboardButton(texts.BTN_ADD_PRODUCT), KeyboardButton(texts.BTN_DELETE_PRODUCT)],
        [KeyboardButton(texts.BTN_ADD_CATEGORY), KeyboardButton(texts.BTN_ALL_ORDERS)],
        [KeyboardButton(texts.BTN_MAIN_MENU)]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_categories_inline_keyboard(prefix="cat"):
    categories = database.get_categories()
    keyboard = []
    row = []
    for cat in categories:
        row.append(InlineKeyboardButton(cat['name'], callback_data=f"{prefix}_{cat['id']}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    if prefix == "cat":
        keyboard.append([InlineKeyboardButton(texts.BTN_MAIN_MENU, callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_products_keyboard(category_id):
    products = database.get_products_by_category(category_id)
    keyboard = []
    row = []
    for prod in products:
        row.append(InlineKeyboardButton(prod['name'], callback_data=f"prod_{prod['id']}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(texts.BTN_BACK, callback_data="back_categories")])
    return InlineKeyboardMarkup(keyboard)

def get_product_delete_keyboard():
    products = database.get_all_products()
    keyboard = []
    row = []
    for prod in products:
        row.append(InlineKeyboardButton(f"❌ {prod['name']}", callback_data=f"delprod_{prod['id']}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def get_product_detail_keyboard(product_id):
    keyboard = [
        [InlineKeyboardButton(texts.BTN_ADD_CART, callback_data=f"addcart_{product_id}")],
        [InlineKeyboardButton("🛒 Savatga o'tish", callback_data="show_cart")],
        [InlineKeyboardButton(texts.BTN_BACK, callback_data="back_categories")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cart_keyboard(cart_items):
    keyboard = []
    for item in cart_items:
        keyboard.append([InlineKeyboardButton(f"❌ {item['name']} x{item['quantity']}", callback_data=f"rmcart_{item['product_id']}")])
    if cart_items:
        keyboard.append([InlineKeyboardButton(texts.BTN_CLEAR_CART, callback_data="clearcart")])
        keyboard.append([InlineKeyboardButton(texts.BTN_CHECKOUT, callback_data="checkout")])
    keyboard.append([
        InlineKeyboardButton("🌐 WEBSITE", url="https://gymfood.robosite.uz/"),
        InlineKeyboardButton("📸 INSTAGRAM", url="https://www.instagram.com/halimjonov_07?igsh=b2VyOTdrY3NpMDE=")
    ])
    keyboard.append([InlineKeyboardButton(texts.BTN_MAIN_MENU, callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_payment_keyboard():
    keyboard = [
        [KeyboardButton(texts.BTN_CASH)],
        [KeyboardButton(texts.BTN_CLICK), KeyboardButton(texts.BTN_PAYME)],
        [KeyboardButton(texts.BTN_MAIN_MENU)]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_contact_keyboard():
    keyboard = [
        [KeyboardButton(texts.BTN_SEND_PHONE, request_contact=True)],
        [KeyboardButton(texts.BTN_MAIN_MENU)]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_keyboard():
    keyboard = [[KeyboardButton(texts.BTN_MAIN_MENU)]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_socials_keyboard():
    keyboard = [
        [InlineKeyboardButton("📸 Instagram", url="https://www.instagram.com/gym_food_oltiariq?igsh=cGRiZGU0azIxZmhp")],
        [InlineKeyboardButton("✈️ Telegram", url="https://t.me/gymfoodoltiariq")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_harid_keyboard():
    keyboard = [
        [InlineKeyboardButton("‎             🌐 WEBSITE             ‎", url="https://gymfood.robosite.uz/")],
        [InlineKeyboardButton("‎             📸 INSTAGRAM             ‎", url="https://www.instagram.com/halimjonov_07?igsh=b2VyOTdrY3NpMDE=")]
    ]
    return InlineKeyboardMarkup(keyboard)
