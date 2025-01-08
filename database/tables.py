from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, func
from sqlalchemy.orm import relationship

from database.database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    subscription_status = Column(String, default='inactive')  # 'active' или 'inactive'
    subscription_expiry = Column(DateTime, nullable=True)

    products = relationship('Product', back_populates='user')


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_name = Column(String)
    product_id = Column(Integer)
    price = Column(Float)

    user = relationship('User', back_populates='products')
    price_history = relationship('PriceHistory', back_populates='product')


class PriceHistory(Base):
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'))
    price = Column(Float)
    timestamp = Column(DateTime, server_default=func.now())

    product = relationship('Product', back_populates='price_history')
