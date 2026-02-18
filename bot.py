import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.types import BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats
from aiogram import BaseMiddleware

from config import BOT_TOKEN
from db import DB
from handlers_private import private_router
from handlers_group import group_router


class InjectMiddleware(BaseMiddleware):
    def __init__(self, db: DB, bot_username: str):
        super().__init__()
        self.db = db
        self.bot_username = bot_username

    async def __call__(self, handler, event, data):
        data["db"] = self.db
        data["bot_username"] = self.bot_username
        return await handler(event, data)


async def set_commands(bot: Bot):
    # Private: faqat /start
    await bot.set_my_commands(
        [BotCommand(command="start", description="Botni ishga tushirish")],
        scope=BotCommandScopeAllPrivateChats())



    # Group: hamma buyruqlar ko‘rinsin (lekin ishlatish faqat admin)
    await bot.set_my_commands(
        [
            BotCommand(command="help", description="Bot buyruqlari"),
            BotCommand(command="mymembers", description="Siz qo‘shgan odamlar soni"),
            BotCommand(command="yourmembers", description="Reply qilingan odam qo‘shganlar soni"),
            BotCommand(command="top", description="Eng ko‘p odam qo‘shgan TOP 10"),
            BotCommand(command="delson", description="Guruhga barcha odam qo'shganlar ma'lumoti tozalandi"),
            BotCommand(command="clean", description="Reply qilingan odamni 0 qilish"),
            BotCommand(command="add", description="Guruhga odam yig‘ish yo‘riqnoma"),
            BotCommand(command="textforce", description="Majburiy matnni o‘zgartirish"),
            BotCommand(command="text_time", description="Majburiy matn o‘chish vaqti"),
            BotCommand(command="deforce", description="Majburiy sozlamalarni default"),
            BotCommand(command="priv", description="Reply qilib imtiyoz berish"),
            BotCommand(command="privs", description="Imtiyoz ro‘yxati"),
            BotCommand(command="set", description="Majburiy a’zolik sozlash"),
            BotCommand(command="unlink", description="Sozlangan kanallarni o‘chirish (namuna)"),
            BotCommand(command="setchannel", description="Kanal boshqaruvi"),

        ],
        scope=BotCommandScopeAllGroupChats()
    )


async def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN yo‘q. .env ni tekshiring.")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    db = DB()
    await db.init()

    me = await bot.get_me()
    bot_username = me.username or ""

    dp.update.middleware(InjectMiddleware(db=db, bot_username=bot_username))

    dp.include_router(private_router)
    dp.include_router(group_router)

    await set_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
