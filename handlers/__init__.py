from aiogram import Router
from .commands import router as commands_router
from .dialogs.registration import router as registration_dialog_router

handlers_router = Router(name="main_handlers_router")

handlers_router.include_routers(commands_router, registration_dialog_router)
