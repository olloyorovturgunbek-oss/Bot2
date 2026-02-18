from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def kb_add_to_group(bot_username: str) -> InlineKeyboardMarkup:
    url = f"https://t.me/{bot_username}?startgroup=1"
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="➕ Guruhga qo‘shing", url=url))
    return kb.as_markup()

def kb_help_group() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⚙️ Sozlash (/set)", callback_data="open_set")
    kb.button(text="🏆 Top 10 (/top)", callback_data="open_top")
    kb.button(text="📊 Mening qo‘shganlarim (/mymembers)", callback_data="open_mymembers")
    kb.adjust(1)
    return kb.as_markup()

def kb_set_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for n in [1, 2, 3, 5, 10]:
        kb.button(text=f"✅ {n} ta", callback_data=f"reqadd:{n}")
    kb.button(text="✍️ Majburiy matnni o‘zgartirish", callback_data="set_force_text")
    kb.button(text="⏳ Matn o‘chish vaqti", callback_data="set_force_text_time")
    kb.button(text="🧹 Majburiy sozlamalarni default", callback_data="deforce")
    kb.adjust(3, 1, 1, 1)
    return kb.as_markup()

def kb_cancel() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Bekor qilish", callback_data="cancel")
    kb.adjust(1)
    return kb.as_markup()

def kb_priv_manage() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📃 Imtiyoz ro‘yxati (/privs)", callback_data="priv_list")
    kb.adjust(1)
    return kb.as_markup()
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def kb_add_required_buttons() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    # 1-qator
    for n in [0, 5, 10, 15, 20]:
        kb.button(text=str(n), callback_data=f"addreq:{n}")

    # 2-qator
    for n in [40, 60, 80, 100]:
        kb.button(text=str(n), callback_data=f"addreq:{n}")

    # bekor qilish
    kb.button(text="❌", callback_data="addreq:cancel")

    kb.adjust(5, 4, 1)
    return kb.as_markup()
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def kb_text_delete_time(selected_seconds: int = 0) -> InlineKeyboardMarkup:
    """
    selected_seconds: hozir tanlangan vaqt (DBdan olinadi)
    """
    options = [
        ("1 min", 60),
        ("2 min", 120),
        ("5 min", 300),
        ("10 min", 600),
    ]

    kb = InlineKeyboardBuilder()

    # 1-qator: 1 min, 2 min
    for label, sec in options[:2]:
        text = f"{label} ✅" if sec == selected_seconds else label
        kb.button(text=text, callback_data=f"txttime:{sec}")

    # 2-qator: 5 min, 10 min
    for label, sec in options[2:]:
        text = f"{label} ✅" if sec == selected_seconds else label
        kb.button(text=text, callback_data=f"txttime:{sec}")

    # 3-qator: cancel
    kb.button(text="❌", callback_data="txttime:cancel")

    kb.adjust(2, 2, 1)
    return kb.as_markup()
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def kb_unlink_channels(channels: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for ch in channels:
        kb.button(text=f"❌ @{ch}", callback_data=f"unlink:{ch}")

    kb.button(text="Yopish", callback_data="unlink:cancel")

    kb.adjust(1)
    return kb.as_markup()
