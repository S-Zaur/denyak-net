from aiogram import Router
from aiogram import html
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext

from db.repository import Repository
from handlers.state import Registration

router = Router(name="commands_router")


@router.message(CommandStart(), StateFilter(None))
async def cmd_start(message: Message, state: FSMContext, repo: Repository):
    user = await repo.user.get_by_id(message.from_user.id)

    if user:
        await message.answer(f"Рад видеть тебя снова, {message.from_user.first_name}\n")
        return
    await repo.user.get_or_create(message.from_user.id, message.from_user.username)
    await repo.commit()
    await state.set_state(Registration.waiting_for_limit)

    sent_msg = await message.answer(
        f"Привет, {html.quote(message.from_user.first_name)}. Добро пожаловать в финансовый трекер <code>Деняк нет</code>\n\n"
        f"Давай настроим твой профиль\n"
        f"<b>Шаг 1 из 3:</b> Введи желаемый лимит трат на месяц (просто число, например <code>30000</code>).\n"
        f"Если не хочешь ставить лимит, напиши <code>0</code>",
        parse_mode=ParseMode.HTML,
    )
    await message.delete()
    await state.update_data(bot_msg_id=sent_msg.message_id)
