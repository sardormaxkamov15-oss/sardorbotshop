import sqlite3
import os

# On Vercel (serverless), the filesystem is read-only except /tmp/
# Use /tmp/ for the database when VERCEL environment variable is set
if os.environ.get("VERCEL"):
    DB_NAME = "/tmp/shop.db"
else:
    DB_NAME = "shop.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # categories
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    ''')
    
    # products
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        name TEXT NOT NULL,
        image_id TEXT,
        price REAL NOT NULL,
        description TEXT,
        quantity INTEGER DEFAULT 0,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    ''')
    
    # users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        full_name TEXT,
        phone_number TEXT,
        language TEXT DEFAULT 'uz',
        is_admin INTEGER DEFAULT 0
    )
    ''')
    
    # cart_items
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        quantity INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users (telegram_id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')
    
    # orders
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        total_price REAL NOT NULL,
        payment_method TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        delivery_address TEXT,
        contact_phone TEXT,
        contact_name TEXT,
        FOREIGN KEY (user_id) REFERENCES users (telegram_id)
    )
    ''')

    # order_items
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        price REAL,
        FOREIGN KEY (order_id) REFERENCES orders (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')

    # Insert default categories if none exist
    cursor.execute('SELECT COUNT(*) FROM categories')
    if cursor.fetchone()[0] == 0:
        default_categories = [
            ("Whey Protein",),
            ("Creatine",),
            ("Amino Acids",),
            ("Pre Workout",),
            ("Mass Gainer",),
            ("Vitamins",),
            ("Fat Burners",),
            ("Accessories",)
        ]
        cursor.executemany('INSERT INTO categories (name) VALUES (?)', default_categories)

    conn.commit()
    conn.close()

# Users table methods
def get_user(telegram_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    user = conn.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)).fetchone()
    conn.close()
    return user

def add_user(telegram_id, full_name=None):
    conn = get_connection()
    try:
        conn.execute('INSERT INTO users (telegram_id, full_name) VALUES (?, ?)', (telegram_id, full_name))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def set_user_phone(telegram_id, phone_number):
    conn = get_connection()
    conn.execute('UPDATE users SET phone_number = ? WHERE telegram_id = ?', (phone_number, telegram_id))
    conn.commit()
    conn.close()

# Categories & Products
def get_categories():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    categories = conn.execute('SELECT * FROM categories').fetchall()
    return categories

def get_category(category_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    category = conn.execute('SELECT * FROM categories WHERE id = ?', (category_id,)).fetchone()
    conn.close()
    return category

def add_category(name):
    conn = get_connection()
    conn.execute('INSERT INTO categories (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()

def get_products_by_category(category_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    products = conn.execute('SELECT * FROM products WHERE category_id = ? AND quantity > 0', (category_id,)).fetchall()
    conn.close()
    return products

def get_all_products():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return products

def get_product(product_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    return product

def add_product(category_id, name, image_id, price, description, quantity):
    conn = get_connection()
    conn.execute('''
        INSERT INTO products (category_id, name, image_id, price, description, quantity) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (category_id, name, image_id, price, description, quantity))
    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = get_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()

# Cart
def get_cart(user_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cart = conn.execute('''
        SELECT c.id as cart_id, p.id as product_id, p.name, p.price, c.quantity, (p.price * c.quantity) as total
        FROM cart_items c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = ?
    ''', (user_id,)).fetchall()
    conn.close()
    return cart

def add_to_cart(user_id, product_id, quantity=1):
    conn = get_connection()
    item = conn.execute('SELECT id, quantity FROM cart_items WHERE user_id = ? AND product_id = ?', (user_id, product_id)).fetchone()
    if item:
        conn.execute('UPDATE cart_items SET quantity = quantity + ? WHERE id = ?', (quantity, item[0]))
    else:
        conn.execute('INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)', (user_id, product_id, quantity))
    conn.commit()
    conn.close()

def remove_from_cart(user_id, product_id):
    conn = get_connection()
    conn.execute('DELETE FROM cart_items WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    conn.commit()
    conn.close()

def clear_cart(user_id):
    conn = get_connection()
    conn.execute('DELETE FROM cart_items WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# Order
def create_order(user_id, total_price, payment_method, delivery_address, contact_phone, contact_name, cart_items):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (user_id, total_price, payment_method, delivery_address, contact_phone, contact_name)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, total_price, payment_method, delivery_address, contact_phone, contact_name))
    order_id = cursor.lastrowid
    
    for item in cart_items:
        cursor.execute('''
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (?, ?, ?, ?)
        ''', (order_id, item['product_id'], item['quantity'], item['price']))
        # update product quantity
        cursor.execute('UPDATE products SET quantity = quantity - ? WHERE id = ?', (item['quantity'], item['product_id']))
        
    cursor.execute('DELETE FROM cart_items WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    return order_id

def get_orders(user_id=None):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    if user_id:
        orders = conn.execute('SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()
    else:
        orders = conn.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()
    conn.close()
    return orders

def get_order_items(order_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    items = conn.execute('''
        SELECT oi.*, p.name 
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    ''', (order_id,)).fetchall()
    conn.close()
    return items
