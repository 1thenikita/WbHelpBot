from datetime import datetime

from sqlalchemy import func, select

from database.database import SessionLocal
from database.tables import User, Product, PriceHistory
from services.wildberries import get_product_price


def add_user(telegram_id, username):
    """
    Функция добавления пользователя в БД.

    :param telegram_id: Telegram ID
    :param username: Username
    :return:
    """

    session = SessionLocal()

    # Проверяем, существует ли пользователь
    existing_user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not existing_user:
        new_user = User(telegram_id=telegram_id, username=username)
        session.add(new_user)  # Добавляем нового пользователя в сессию
        session.commit()  # Сохраняем изменения в базе данных
        print("Пользователь добавлен.")
    else:
        raise Exception("Пользователь уже существует.")

    session.close()


def add_product(user_id, product_name, product_id, price):
    status, expired = get_user_subscription(user_id)
    # Проверяем количество товаров
    if count_user_products(user_id) > 3 and status == 'inactive':  # Ограничение для бесплатных пользователей
        raise Exception("Достигнуто максимальное количество отслеживаемых товаров.")

    session = SessionLocal()

    existing_product = session.query(Product).filter_by(product_id=product_id).first()

    if not existing_product:
        new_product = Product(user_id=user_id, product_name=product_name, price=price, product_id=product_id)
        session.add(new_product)
        session.commit()
    else:
        raise Exception("Продукт уже существует.")

    session.close()


def get_all_products():
    session = SessionLocal()
    products = session.query(Product).all()
    session.close()
    return products


def get_products(user_id):
    session = SessionLocal()
    products = session.query(Product).filter_by(user_id=user_id).all()
    session.close()
    return products


def get_product_info(product_id):
    session = SessionLocal()
    products = session.query(Product).filter_by(product_id=product_id).first()
    session.close()
    return products

def delete_product(user_id, product_id):
    session = SessionLocal()

    session.query(Product).filter_by(user_id=user_id, product_id=product_id).delete()
    session.commit()
    session.close()


def update_price(product_id):
    # Получаем текущую цену (предполагается, что функция get_price уже существует)
    session = SessionLocal()

    current_price = float(get_product_price(product_id))

    # Добавляем запись в таблицу истории цен
    new_price_history_entry = PriceHistory(product_id=product_id, price=current_price)
    session.add(new_price_history_entry)  # Добавляем новую запись в сессию
    session.commit()  # Сохраняем изменения в базе данных

    session.query(Product).filter_by(product_id=product_id).update({PriceHistory.price: current_price})
    session.commit()

    # Закрываем сессию
    session.close()


def get_last_price(product_id):
    """
    Получить последнюю цену товара

    :param product_id:
    :return
    """
    session = SessionLocal()

    try:
        # Формируем запрос для получения последней цены
        stmt = (
            select(Product.price)
            .where(Product.product_id == product_id)
            .limit(1)
        )

        result = session.execute(stmt).scalar_one_or_none()  # Выполняем запрос и получаем результат
        return result  # Вернем цену или None, если запись не найдена
    finally:
        session.close()  # Закрываем сессию


def update_all_prices():
    session = SessionLocal()
    # Получаем все отслеживаемые товары
    products = session.query(Product).all()
    session.close()

    for product in products:
        update_price(product.product_id)


def get_price_history(product_id):
    """Получить историю цен товара"""
    session = SessionLocal()  # Создаем новую сессию
    try:
        # Выполняем запрос к базе данных
        history = (session.query(PriceHistory.timestamp, PriceHistory.price)
                   .filter(PriceHistory.product_id == product_id)
                   .order_by(PriceHistory.timestamp.desc())
                   .limit(10))
        return history  # Возвращаем результаты
    finally:
        session.close()  # Закрываем сессию


def get_product_details(product_id):
    """Получить данные товара"""
    session = SessionLocal()  # Создаем новую сессию
    try:
        # Выполняем запрос к базе данных
        result = (session.query(Product.product_name, Product.product_id)
                  .filter(Product.product_id == product_id)
                  .one_or_none())  # Получаем одну запись или None
        if result:
            return {
                "name": result[0],
                "id": result[1],
            }
    finally:
        session.close()  # Закрываем сессию
    return None


def count_user_products(user_id):
    """Подсчитать количество товаров у пользователя"""
    session = SessionLocal()  # Создаем новую сессию
    try:
        # Выполняем запрос к базе данных
        count = (session.query(func.count(Product.product_id))
                 .filter(Product.user_id == user_id)
                 .scalar())  # Получаем единственное значение
        return count
    finally:
        session.close()  # Закрываем сессию


def update_subscription(telegram_id: int, status: str, expiry_date: datetime):
    """
    Обновляет статус подписки пользователя в базе данных.

    :param telegram_id: Telegram ID пользователя.
    :param status: Новый статус подписки ('active' или 'inactive').
    :param expiry_date: Дата окончания подписки.
    """
    session = SessionLocal()  # Создаем новую сессию
    try:
        # Проверяем, существует ли пользователь
        user = session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
        if user is None:
            raise Exception("Пользователь не найден в базе данных.")

        # Обновляем данные подписки
        user.subscription_status = status
        user.subscription_expiry = expiry_date

        session.commit()
    except Exception as e:
        print(f"Ошибка при обновлении подписки: {e}")
        session.rollback()  # Откатываем изменения в случае ошибки
    finally:
        session.close()  # Закрываем сессию



def get_user_subscription(telegram_id: int):
    """
    Получает информацию о подписке пользователя.

    :param telegram_id: Telegram ID пользователя.
    :return: Кортеж (статус подписки, дата окончания) или None.
    """
    session = SessionLocal()  # Создаем новую сессию
    try:
        # Получаем пользователя по telegram_id
        user = session.query(User).filter(User.telegram_id == telegram_id).one_or_none()

        if user is None:
            return None  # Если пользователь не найден, возвращаем None

        # Возвращаем статус подписки и дату окончания
        return user.subscription_status, user.subscription_expiry
    except Exception as e:
        print(f"Ошибка при получении подписки: {e}")
        return None
    finally:
        session.close()  # Закрываем сессию
