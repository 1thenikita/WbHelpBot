# keyboards.py
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardBuilder


def main_menu_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text=("Добавить товар"),callback_data='add')
    keyboard.button(text=("Список отслеживаемых"),callback_data='list')
    keyboard.button(text=("Удалить товар"),callback_data='delete')
    keyboard.button(text=("Помощь"),callback_data='help')
    return keyboard.as_markup()
