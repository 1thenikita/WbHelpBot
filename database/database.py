# db.py
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logging.basicConfig(level=logging.INFO)

# Создание базы данных
Base = declarative_base()

db_url="sqlite:///wildberries_bot.sqlite"
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """
    Функция инициализации работы БД.
    Добавление таблиц.
    :param db_url:
    :return:
    """

    # Создаем таблицы
    try:
        Base.metadata.create_all(bind=engine)
        logging.info('Таблицы успешно созданы!')
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
        raise
