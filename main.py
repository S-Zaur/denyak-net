import asyncio

from aiogram.client.session.aiohttp import AiohttpSession

from aiogram import Bot, Dispatcher
from handlers import handlers_router
from config import BOT_TOKEN, PROXY
from db.middleware import DbSessionMiddleware
from db.database import init_models, async_session

session = AiohttpSession()
if PROXY:
    session = AiohttpSession(proxy=PROXY)

bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()


async def main():
    await init_models()

    dp.update.middleware(DbSessionMiddleware(session_pool=async_session))
    dp.include_router(handlers_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
