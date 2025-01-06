# db.py
import sqlite3

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
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


def add_user(telegram_id, username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)", (telegram_id, username))
    conn.commit()
    conn.close()


def add_product(user_id, product_name, product_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (user_id, product_name, product_id) VALUES (?, ?, ?)",
                   (user_id, product_name, product_id))
    conn.commit()
    conn.close()


def get_products(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, product_id FROM products WHERE user_id = ?", (user_id,))
    products = cursor.fetchall()
    conn.close()
    return products


def delete_product(user_id, product_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    conn.commit()
    conn.close()


# Инициализация базы данных
init_db()