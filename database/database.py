# db.py
import sqlite3

from services.wildberries import get_product_price

DB_PATH = "wildberries_bot.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Создаем таблицу для пользователей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER UNIQUE,
        username TEXT
    )
    """)

    # Создаем таблицу для отслеживаемых товаров
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        product_name TEXT,
        product_id INTEGER,
        price REAL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_history (
        id INTEGER PRIMARY KEY,
        product_id INTEGER,
        price REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    )""")

    conn.commit()
    conn.close()


def add_user(telegram_id, username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)", (telegram_id, username))
    conn.commit()
    conn.close()


def add_product(user_id, product_name, product_id, price):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (user_id, product_name, product_id, price) VALUES (?, ?, ?, ?)",
                   (user_id, product_name, product_id, price))
    conn.commit()
    conn.close()


def get_products(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, product_id, price FROM products WHERE user_id = ?", (user_id,))
    products = cursor.fetchall()
    conn.close()
    return products


def delete_product(user_id, product_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    conn.commit()
    conn.close()


def update_price(product_id):
    # Получаем текущую цену (предполагается, что функция get_price уже существует)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    current_price = float(get_product_price(product_id)) / 100

    # Добавляем запись в таблицу истории цен
    cursor.execute("""
        INSERT INTO price_history (product_id, price)
        VALUES (?, ?)
    """, (product_id, current_price))

    conn.commit()
    conn.close()


def update_all_prices():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Получаем все отслеживаемые товары
    cursor.execute("SELECT product_id FROM products")
    products = cursor.fetchall()

    conn.close()

    for product in products:
        product_id = product[0]
        update_price(product_id)


# Инициализация базы данных
init_db()
