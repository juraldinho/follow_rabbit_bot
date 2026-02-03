import re
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from config import load_config
from states import OrderForm
from keyboards import cities_kb, hotels_kb, confirm_kb, phone_request_kb

PHONE_RE = re.compile(r"^\+?\d[\d\s\-\(\)]{7,}$")

def format_order(data: dict) -> str:
    cities = ", ".join(data.get("cities", [])) or "—"
    dates = data.get("dates", "—")
    hotel = data.get("hotel", "—")
    name = data.get("name", "—")
    phone = data.get("phone", "—")
    comment = data.get("comment", "—")

    return (
        "🐇 Follow the Rabbit — Новая заявка\n\n"
        f"🏙 Города: {cities}\n"
        f"📅 Даты: {dates}\n"
        f"🏨 Отель: {hotel}\n"
        f"👤 Имя: {name}\n"
        f"📞 Телефон: {phone}\n"
        f"📝 Комментарий: {comment}\n\n"
        f"⏱ Время: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    )

async def start_new_order(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(OrderForm.cities)
    await state.update_data(cities=[])
    await message.answer(
        "Привет! Я помогу быстро собрать заявку 😊\n\n"
        "1) Выберите города, которые хотите посетить (можно несколько):",
        reply_markup=cities_kb(set()),
    )

async def main():
    cfg = load_config()
    bot = Bot(token=cfg.bot_token)
    dp = Dispatcher()

    @dp.message(Command("chatid"))
    async def cmd_chatid(message: Message):
        await message.answer(f"chat_id = {message.chat.id}")


    # /start
    @dp.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext):
        await start_new_order(message, state)

    # /new
    @dp.message(Command("new"))
    async def cmd_new(message: Message, state: FSMContext):
        await start_new_order(message, state)

    # --- STEP 1: Cities (multi-select) ---
    @dp.callback_query(OrderForm.cities, F.data.startswith("city:"))
    async def on_city_toggle(call: CallbackQuery, state: FSMContext):
        city = call.data.split(":", 1)[1]
        data = await state.get_data()
        cities = set(data.get("cities", []))

        if city in cities:
            cities.remove(city)
        else:
            cities.add(city)

        await state.update_data(cities=sorted(cities))
        await call.message.edit_reply_markup(reply_markup=cities_kb(cities))
        await call.answer()

    @dp.callback_query(OrderForm.cities, F.data == "cities:reset")
    async def on_cities_reset(call: CallbackQuery, state: FSMContext):
        await state.update_data(cities=[])
        await call.message.edit_reply_markup(reply_markup=cities_kb(set()))
        await call.answer("Сброшено")

    @dp.callback_query(OrderForm.cities, F.data == "cities:done")
    async def on_cities_done(call: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        cities = data.get("cities", [])
        if not cities:
            await call.answer("Выберите хотя бы 1 город 🙂", show_alert=True)
            return

        await state.set_state(OrderForm.dates)
        await call.message.answer(
            "2) Напишите даты поездки в любом удобном формате.\n"
            "Например: `10–15 марта` или `10.03–15.03`",
        )
        await call.answer()

    # --- STEP 2: Dates (text) ---
    @dp.message(OrderForm.dates)
    async def on_dates(message: Message, state: FSMContext):
        text = (message.text or "").strip()
        if len(text) < 3:
            await message.answer("Пожалуйста, напишите даты чуть понятнее 🙂")
            return

        await state.update_data(dates=text)
        await state.set_state(OrderForm.hotel)
        await message.answer("3) Выберите звездность отеля:", reply_markup=hotels_kb())

    # --- STEP 3: Hotel (buttons) ---
    @dp.callback_query(OrderForm.hotel, F.data.startswith("hotel:"))
    async def on_hotel(call: CallbackQuery, state: FSMContext):
        hotel = call.data.split(":", 1)[1]
        await state.update_data(hotel=hotel)
        await state.set_state(OrderForm.name)
        await call.message.answer("4) Как вас зовут? (Имя)")
        await call.answer()

    # --- STEP 4: Name (text) ---
    @dp.message(OrderForm.name)
    async def on_name(message: Message, state: FSMContext):
        name = (message.text or "").strip()
        if len(name) < 2:
            await message.answer("Имя слишком короткое 🙂 Напишите, пожалуйста, еще раз.")
            return

        await state.update_data(name=name)
        await state.set_state(OrderForm.phone)
        await message.answer(
            "5) Отправьте номер телефона.\n"
            "Можно нажать кнопку ниже или написать вручную (например: +998901234567).",
            reply_markup=phone_request_kb(),
        )

    # --- STEP 5: Phone (contact or text) ---
    @dp.message(OrderForm.phone, F.contact)
    async def on_phone_contact(message: Message, state: FSMContext):
        phone = message.contact.phone_number.strip()
        await state.update_data(phone=phone)
        await state.set_state(OrderForm.comment)
        await message.answer("6) Комментарий/пожелания? Если нет — напишите `-`.", reply_markup=None)

    @dp.message(OrderForm.phone)
    async def on_phone_text(message: Message, state: FSMContext):
        phone = (message.text or "").strip()
        if not PHONE_RE.match(phone):
            await message.answer("Похоже, номер некорректный. Пример: +998901234567\nПопробуйте еще раз.")
            return

        await state.update_data(phone=phone)
        await state.set_state(OrderForm.comment)
        await message.answer("6) Комментарий/пожелания? Если нет — напишите `-`.", reply_markup=None)

    # --- STEP 6: Comment (text) ---
    @dp.message(OrderForm.comment)
    async def on_comment(message: Message, state: FSMContext):
        comment = (message.text or "").strip()
        if comment == "-":
            comment = "—"

        await state.update_data(comment=comment)
        data = await state.get_data()

        # показать резюме и попросить подтверждение
        cities = ", ".join(data.get("cities", []))
        summary = (
            "Проверьте заявку:\n\n"
            f"🏙 Города: {cities}\n"
            f"📅 Даты: {data.get('dates')}\n"
            f"🏨 Отель: {data.get('hotel')}\n"
            f"👤 Имя: {data.get('name')}\n"
            f"📞 Телефон: {data.get('phone')}\n"
            f"📝 Комментарий: {data.get('comment')}\n"
        )

        await state.set_state(OrderForm.confirm)
        await message.answer(summary, reply_markup=confirm_kb())

    # --- STEP 7: Confirm ---
    @dp.callback_query(OrderForm.confirm, F.data == "confirm:restart")
    async def on_restart(call: CallbackQuery, state: FSMContext):
        await call.answer("Ок, начнем заново")
        await start_new_order(call.message, state)

    @dp.callback_query(OrderForm.confirm, F.data == "confirm:yes")
    async def on_confirm(call: CallbackQuery, state: FSMContext):
        data = await state.get_data()

        # 1) Клиенту
        await call.message.answer(
            "Спасибо! ✅\n"
            "Мы подготовим предложение и свяжемся с вами в ближайшее время.",
            reply_markup=None,
        )

        # 2) Админу
        cfg = load_config()
        admin_text = format_order(data)

        if call.from_user.username:
            admin_text += f"\n👤 TG: @{call.from_user.username}"
        admin_text += f"\n🆔 user_id: `{call.from_user.id}`"

        await call.bot.send_message(cfg.admin_id, admin_text)

        await state.clear()
        await call.answer("Отправлено ✅")


    # Запуск
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

