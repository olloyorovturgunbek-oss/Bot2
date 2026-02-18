from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError


async def is_admin_chat(bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except (TelegramBadRequest, TelegramForbiddenError):
        # Bot admin emas / chatga kira olmaydi / huquqi yo‘q
        return False


class AdminOnly(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if not message.from_user:
            return False
        return await is_admin_chat(message.bot, message.chat.id, message.from_user.id)


async def cb_is_admin(call: CallbackQuery) -> bool:
    if not call.from_user or not call.message:
        return False
    return await is_admin_chat(call.bot, call.message.chat.id, call.from_user.id)
