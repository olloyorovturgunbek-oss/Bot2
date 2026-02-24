from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# =========================
#  BOTNI GURUHGA QO‘SHISH
# =========================
def kb_add_to_group(bot_username: str) -> InlineKeyboardMarkup:
    bot_username = (bot_username or "").strip().lstrip("@")
    url = f"https://t.me/{bot_username}?startgroup=1"
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="➕ Guruhga qo‘shing", url=url))
    return kb.as_markup()


# =========================
#  HELP (ADMIN PANEL)
# =========================
def kb_help_group() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⚙️ Sozlash (/set)", callback_data="open_set")
    kb.button(text="🏆 Top 10 (/top)", callback_data="open_top")
    kb.button(text="📊 Mening qo‘shganlarim (/mymembers)", callback_data="open_mymembers")
    kb.adjust(1)
    return kb.as_markup()


# =========================
#  /SET MENU
# =========================
def kb_set_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    # talab (required_adds) tanlash
    for n in [1, 2, 3, 5, 10]:
        kb.button(text=f"✅ {n} ta", callback_data=f"reqadd:{n}")

    kb.button(text="✍️ Majburiy matnni o‘zgartirish", callback_data="set_force_text")
    kb.button(text="⏳ Matn o‘chish vaqti", callback_data="set_force_text_time")
    kb.button(text="🧹 Majburiy sozlamalarni default", callback_data="deforce")

    kb.adjust(3, 2, 1, 1, 1)
    return kb.as_markup()


# =========================
#  CANCEL
# =========================
def kb_cancel() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Bekor qilish", callback_data="cancel")
    kb.adjust(1)
    return kb.as_markup()


# =========================
#  PRIVILEGE MENU
# =========================
def kb_priv_manage() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📃 Imtiyoz ro‘yxati (/privs)", callback_data="priv_list")
    kb.adjust(1)
    return kb.as_markup()


# =========================
#  /ADD (required_adds) BUTTONS
# =========================
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


# =========================
#  FORCE TEXT DELETE TIME
# =========================
def kb_text_delete_time(selected_seconds: int = 0) -> InlineKeyboardMarkup:
    options = [
        ("1 min", 60),
        ("2 min", 120),
        ("5 min", 300),
        ("10 min", 600),
    ]

    kb = InlineKeyboardBuilder()

    # 1-qator: 1 min, 2 min
    for label, sec in options[:2]:
        text = f"{label} ✅" if sec == int(selected_seconds) else label
        kb.button(text=text, callback_data=f"txttime:{sec}")

    # 2-qator: 5 min, 10 min
    for label, sec in options[2:]:
        text = f"{label} ✅" if sec == int(selected_seconds) else label
        kb.button(text=text, callback_data=f"txttime:{sec}")

    kb.button(text="❌", callback_data="txttime:cancel")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


# =========================
#  UNLINK CHANNELS
# =========================
def kb_unlink_channels(channels: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for ch in channels:
        ch = (ch or "").strip().lstrip("@")
        if ch:
            kb.button(text=f"❌ @{ch}", callback_data=f"unlink:{ch}")

    kb.button(text="Yopish", callback_data="unlink:cancel")
    kb.adjust(1)
    return kb.as_markup()


# =========================
#  PROGRESS (REALTIME)
# =========================
def kb_progress(added: int, required: int, target_user_id: int) -> InlineKeyboardMarkup:
    added = int(added)
    required = max(int(required), 0)
    target_user_id = int(target_user_id)

    left = max(required - added, 0)
    percent = 0
    if required > 0:
        percent = min(int((added / required) * 100), 100)

    kb = InlineKeyboardBuilder()
    kb.button(
        text=f"📊 {added}/{required} | Qoldi: {left} | {percent}%",
        callback_data="noop",
    )
    kb.button(text="✅ Odam qo‘shdim (tekshir)", callback_data=f"check_added:{target_user_id}")
    kb.button(text="🔄 Yangilash", callback_data=f"check_added:{target_user_id}")

    # ✅ replysiz imtiyoz: user_id callback_data ichida
    kb.button(text="🧑‍💼 Imtiyoz berish", callback_data=f"give_priv:{target_user_id}")

    kb.adjust(1, 2, 1)
    return kb.as_markup()
