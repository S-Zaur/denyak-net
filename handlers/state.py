from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_for_limit = State()
    waiting_for_timezone = State()
    waiting_for_timezone_choice = State()
    waiting_for_time = State()
