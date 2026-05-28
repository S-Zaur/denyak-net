import datetime

from aiogram import F, Router
from aiogram import html
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from timezonefinder import TimezoneFinder
from aiogram.utils.markdown import markdown_decoration as md

from db.repository import Repository
from handlers.state import Registration
from handlers import keyboards as kb

router = Router(name="registration_dialog_router")


# ================================
# ШАГ 1 Получение месячного лимита
# ================================
@router.message(Registration.waiting_for_limit)
async def process_limit(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    bot_msg_id = data.get("bot_msg_id")

    try:
        await message.bot.delete_message(
            chat_id=message.chat.id, message_id=message.message_id
        )
    except:
        pass

    if not text.isdigit():
        msg = await message.bot.edit_message_text(
            text="Пожалуйста, введи целое число без букв и пробелов",
            chat_id=message.chat.id,
            message_id=bot_msg_id,
        )
        await state.update_data(bot_msg_id=msg.message_id)
        return

    limit_value = float(text)
    monthly_limit = None if limit_value == 0 else limit_value

    await state.update_data(monthly_limit=monthly_limit)
    await state.set_state(Registration.waiting_for_timezone)
    sent_reply = await message.bot.edit_message_text(
        f"<b>Шаг 2 из 3:</b> Теперь настроим твой часовой пояс\n",
        chat_id=message.chat.id,
        message_id=bot_msg_id,
        reply_markup=kb.timezone_inline_keyboard,
        parse_mode=ParseMode.HTML,
    )
    await state.update_data(choice_geo_msg_id=sent_reply.message_id)


# ==============================
# ШАГ 2 Получение часового пояса
# ==============================
@router.callback_query(Registration.waiting_for_timezone, F.data.startswith("tz:"))
async def process_timezone_callback(callback: CallbackQuery, state: FSMContext):
    user_tz = callback.data.split(":")[1]
    if user_tz == "Dont/Know":
        await callback.message.edit_reply_markup(
            "Тогда можем сделать так:", reply_markup=kb.dont_know_kb
        )
        return
    await state.update_data(timezone=user_tz)
    await callback.answer()
    await next_step_notification(callback.message, state, user_tz)


@router.message(Registration.waiting_for_timezone, F.location)
async def process_timezone_geo(message: Message, state: FSMContext):
    tf = TimezoneFinder()
    user_tz = (
        tf.timezone_at(lng=message.location.longitude, lat=message.location.latitude)
        or "Europe/Moscow"
    )
    await state.update_data(timezone=user_tz)
    await next_step_notification(message, state, user_tz)


@router.callback_query(Registration.waiting_for_timezone, F.data == "tz_choice:geo")
async def tz_choice_geo(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    sent_reply = await callback.message.answer(
        "Нажми на появившуюся внизу <b>Отправить геолокацию</b>, чтобы я узнал твой часовой пояс автоматически",
        reply_markup=kb.location_kb,
        parse_mode=ParseMode.HTML,
    )
    await state.update_data(geo_status_msg_id=sent_reply.message_id)


@router.callback_query(Registration.waiting_for_timezone, F.data == "tz_choice:default")
async def tz_choice_default(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Установлено время по умолчанию")
    await state.update_data(timezone="Europe/Moscow")
    await next_step_notification(callback.message, state, "Europe/Moscow")


async def next_step_notification(message: Message, state: FSMContext, user_tz: str):
    data = await state.get_data()
    choice_geo_msg_id = data.get("choice_geo_msg_id")
    geo_status_msg_id = data.get("geo_status_msg_id")
    if geo_status_msg_id:
        await message.bot.delete_message(
            chat_id=message.chat.id, message_id=geo_status_msg_id
        )
        await message.delete()
    await state.set_state(Registration.waiting_for_time)
    msg = await message.bot.edit_message_text(
        f"Часовой пояс установлен: <b>{html.quote(user_tz)}</b>\n\n"
        f"<b>Шаг 3 из 3:</b> Во сколько присылать сводку за вчерашний день?\n"
        f"Введи время в формате ЧЧ:ММ (например <code>09:00</code>)",
        chat_id=message.chat.id,
        message_id=choice_geo_msg_id,
        parse_mode=ParseMode.HTML,
    )
    await state.update_data(last_msg=msg.message_id)


# ===================================
# ШАГ 3 Получение времени уведомлений
# ===================================
@router.message(Registration.waiting_for_time)
async def process_notification_time(
    message: Message, state: FSMContext, repo: Repository
):
    text = message.text.strip()
    data = await state.get_data()
    try:
        notification_time = datetime.datetime.strptime(text, "%H:%M").time()
    except ValueError:
        await message.bot.delete_message(
            chat_id=message.chat.id, message_id=data.get("last_msg")
        )
        await message.delete()
        msg = await message.answer(
            f"Неверный формат. Введи время в формате ЧЧ:ММ (например <code>07:40</code>)",
            parse_mode=ParseMode.HTML,
        )
        await state.update_data(last_msg=msg.message_id)
        return
    await message.answer("Настройка профиля завершена")
    await message.bot.delete_message(
        chat_id=message.chat.id, message_id=data.get("last_msg")
    )
    await message.delete()
    user_data = await state.get_data()
    await repo.user.update_user_settings(
        tg_id=message.from_user.id,
        monthly_limit=user_data.get("monthly_limit"),
        timezone=user_data.get("timezone"),
        notification_time=notification_time,
    )
    await repo.commit()
    await state.clear()
