from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

CITIES = ["Самарканд", "Бухара", "Хива", "Ташкент"]
HOTELS = ["3★", "4★", "5★", "Любой"]

def cities_kb(selected: set[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for city in CITIES:
        mark = "✅ " if city in selected else ""
        kb.add(InlineKeyboardButton(text=f"{mark}{city}", 
callback_data=f"city:{city}"))

    kb.add(InlineKeyboardButton(text="➡️ Готово", 
callback_data="cities:done"))
    kb.add(InlineKeyboardButton(text="🔄 Сбросить", 
callback_data="cities:reset"))
    kb.adjust(2)
    return kb.as_markup()

def hotels_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for h in HOTELS:
        kb.add(InlineKeyboardButton(text=h, callback_data=f"hotel:{h}"))
    kb.adjust(2)
    return kb.as_markup()

def confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="✅ Подтвердить", 
callback_data="confirm:yes"))
    kb.add(InlineKeyboardButton(text="✏️ Начать заново", 
callback_data="confirm:restart"))
    kb.adjust(1)
    return kb.as_markup()

def phone_request_kb() -> ReplyKeyboardMarkup:
    # Кнопка "поделиться контактом"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📲 Отправить мой номер", 
request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
        selective=True,
    )

