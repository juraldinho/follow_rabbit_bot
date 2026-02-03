from aiogram.fsm.state import State, StatesGroup

class OrderForm(StatesGroup):
    cities = State()
    dates = State()
    hotel = State()
    name = State()
    phone = State()
    comment = State()
    confirm = State()

