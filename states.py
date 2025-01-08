from aiogram.fsm.state import StatesGroup, State

class AddProductState(StatesGroup):
    waiting_for_product_name = State()