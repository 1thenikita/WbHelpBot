# db.py
import sqlite3
from datetime import datetime

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
        username TEXT,
        subscription_status TEXT DEFAULT 'inactive', -- 'active' или 'inactive'
        subscription_expiry TIMESTAMP NULL -- Дата окончания подписки
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
    # Проверяем количество товаров
    if count_user_products(user_id) >= 3:  # Ограничение для бесплатных пользователей
        raise Exception("Достигнуто максимальное количество отслеживаемых товаров.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (user_id, product_name, product_id, price) VALUES (?, ?, ?, ?)",
                   (user_id, product_name, product_id, price))
    conn.commit()
    conn.close()


def get_all_products():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, product_id, price FROM products",)
    products = cursor.fetchall()
    conn.close()
    return products

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

    current_price = float(get_product_price(product_id))

    # Добавляем запись в таблицу истории цен
    cursor.execute("""
        INSERT INTO price_history (product_id, price)
        VALUES (?, ?)
    """, (product_id, current_price))

    conn.commit()
    conn.close()

def get_last_price(product_id):
    """Получить последнюю цену товара"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT price FROM price_history
    WHERE product_id = ?
    ORDER BY timestamp DESC
    LIMIT 1
    """, (product_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def add_price_history(product_id, price):
    """Добавить запись в историю цен"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO price_history (product_id, price, timestamp)
    VALUES (?, ?, datetime('now'))
    """, (product_id, price))
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

def get_price_history(product_id):
    """Получить историю цен товара"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT timestamp, price FROM price_history
    WHERE product_id = ?
    ORDER BY timestamp DESC
    """, (product_id,))
    history = cursor.fetchall()
    conn.close()
    return history

def get_product_details(product_id):
    """Получить данные товара"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT product_name, product_id
    FROM products
    WHERE product_id = ?
    """, (product_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            "name": result[0],
            "id": result[1],
        }
    return None

def count_user_products(user_id):
    """Подсчитать количество товаров у пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT COUNT(*) FROM products
    WHERE user_id = ?
    """, (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def update_subscription(telegram_id: int, status: str, expiry_date: datetime):
    """
    Обновляет статус подписки пользователя в базе данных.

    :param telegram_id: Telegram ID пользователя.
    :param status: Новый статус подписки ('active' или 'inactive').
    :param expiry_date: Дата окончания подписки.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        expiry_date_str = expiry_date.strftime('%Y-%m-%d %H:%M:%S')

        # Проверяем, существует ли пользователь
        cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id = ?", (telegram_id,))
        if cursor.fetchone()[0] == 0:
            print("Пользователь не найден в базе данных.")
            return

        # Обновляем данные подписки
        cursor.execute("""
            UPDATE users
            SET subscription_status = ?, subscription_expiry = ?
            WHERE telegram_id = ?
        """, (status, expiry_date_str, telegram_id))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении подписки: {e}")
    finally:
        conn.close()

def get_user_subscription(telegram_id: int):
    """
    Получает информацию о подписке пользователя.

    :param telegram_id: Telegram ID пользователя.
    :return: Кортеж (статус подписки, дата окончания) или None.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT subscription_status, subscription_expiry
            FROM users
            WHERE telegram_id = ?
        """, (telegram_id,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Ошибка при получении подписки: {e}")
        return None
    finally:
        conn.close()

# Инициализация базы данных
init_db()
