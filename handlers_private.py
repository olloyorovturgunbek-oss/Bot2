from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards import kb_add_to_group

private_router = Router()

@private_router.message(CommandStart())
async def start_private(message: Message, bot_username: str):
    text = (
        "✅ Bot tayyor!\n\n"
        "Guruhda ishlashi uchun botni guruhga qo‘shing va ADMIN qiling.\n"
        "Keyin guruhda /help yozing."
    )
    await message.answer(text, reply_markup=kb_add_to_group(bot_username))
