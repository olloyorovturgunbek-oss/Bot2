import asyncio
from typing import Dict, Tuple, List

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import DB
from states import ForceTextState, ForceTextTimeState
from admin_filters import AdminOnly, cb_is_admin

from keyboards import (
    kb_help_group,
    kb_set_menu,
    kb_cancel,
    kb_add_required_buttons,
    kb_text_delete_time,
    kb_unlink_channels,
    kb_progress,
)

group_router = Router()

# (chat_id, user_id) -> warning_message_id
_last_warn_msg: Dict[Tuple[int, int], int] = {}


# =========================
#   HELPERS: channel subscribe check
# =========================
def kb_join_channels(channels: List[str]) -> InlineKeyboardMarkup:
    rows = []
    for ch in channels:
        ch = ch.lstrip("@")
        rows.append([InlineKeyboardButton(text=f"➡️ @{ch}", url=f"https://t.me/{ch}")])
    rows.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def is_subscribed_all(bot, user_id: int, channels: List[str]) -> bool:
    for ch in channels:
        ch = ch.lstrip("@")
        try:
            member = await bot.get_chat_member(chat_id=f"@{ch}", user_id=user_id)
            if member.status in ("left", "kicked"):
                return False
        except Exception:
            return False
    return True


# =========================
#   /setchannel (KANAL PANEL)
# =========================
def kb_setchannel_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Kanal qo‘shish", callback_data="sc:add")
    kb.button(text="📋 Kanallar ro‘yxati", callback_data="sc:list")
    kb.button(text="❌ Kanal o‘chirish", callback_data="sc:del")
    kb.button(text="✖️ Yopish", callback_data="sc:close")
    kb.adjust(1)
    return kb.as_markup()


def kb_delete_channels(channels: List[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for ch in channels:
        ch = ch.lstrip("@")
        kb.button(text=f"❌ @{ch}", callback_data=f"sc:del:{ch}")
    kb.button(text="✖️ Yopish", callback_data="sc:close")
    kb.adjust(1)
    return kb.as_markup()


@group_router.message(Command("setchannel"))
async def setchannel_menu(message: Message, db: DB):
    if not await AdminOnly()(message):
        return await message.reply("admin")

    channels = await db.get_channels(message.chat.id)
    await message.reply(
        f"📢 <b>Kanal boshqaruvi</b>\n\nUlangan kanallar: <b>{len(channels)}</b>\n\nTanlang:",
        reply_markup=kb_setchannel_menu(),
    )


@group_router.callback_query(F.data == "sc:add")
async def sc_add(call: CallbackQuery):
    if not call.message:
        return
    if not await cb_is_admin(call):
        return await call.answer("admin", show_alert=True)

    await call.message.edit_text(
        "➕ Kanal username yuboring.\n\nMisol:\n@mychannel\n\nBir nechta bo‘lsa:\n@kanal1 @kanal2",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✖️ Yopish", callback_data="sc:close")]
        ]),
    )
    await call.answer()


@group_router.message(F.chat.type.in_({"group", "supergroup"}), F.text.regexp(r"^@"))
async def sc_save_channel(message: Message, db: DB):
    if not await AdminOnly()(message):
        return

    parts = [p.strip() for p in (message.text or "").replace("\n", " ").split() if p.strip()]
    channels: List[str] = []
    for p in parts:
        if p.startswith("@"):
            p = p[1:]
        p = p.lower()
        if p and p not in channels:
            channels.append(p)

    if not channels:
        return await message.reply("❗ Kanal topilmadi. Misol: @mychannel")

    for ch in channels:
        try:
            await db.add_channel(message.chat.id, ch)
        except Exception:
            pass

    await message.reply("✅ Qo‘shildi: " + ", ".join([f"@{c}" for c in channels]))


@group_router.callback_query(F.data == "sc:list")
async def sc_list(call: CallbackQuery, db: DB):
    if not call.message:
        return
    if not await cb_is_admin(call):
        return await call.answer("admin", show_alert=True)

    channels = await db.get_channels(call.message.chat.id)
    if not channels:
        return await call.answer("Kanal yo‘q", show_alert=True)

    text = "📋 <b>Ulangan kanallar:</b>\n\n" + "\n".join([f"• @{c}" for c in channels])
    await call.message.edit_text(text, reply_markup=kb_setchannel_menu())
    await call.answer()


@group_router.callback_query(F.data == "sc:del")
async def sc_del_menu(call: CallbackQuery, db: DB):
    if not call.message:
        return
    if not await cb_is_admin(call):
        return await call.answer("admin", show_alert=True)

    channels = await db.get_channels(call.message.chat.id)
    if not channels:
        return await call.answer("Kanal yo‘q", show_alert=True)

    await call.message.edit_text("❌ Qaysi kanalni o‘chiramiz?", reply_markup=kb_delete_channels(channels))
    await call.answer()


@group_router.callback_query(F.data.startswith("sc:del:"))
async def sc_del(call: CallbackQuery, db: DB):
    if not call.message:
        return
    if not await cb_is_admin(call):
        return await call.answer("admin", show_alert=True)

    ch = call.data.split(":", 2)[2]
    await db.remove_channel(call.message.chat.id, ch)

    channels = await db.get_channels(call.message.chat.id)
    if not channels:
        await call.message.edit_text("✅ Hamma kanallar o‘chirildi.", reply_markup=kb_setchannel_menu())
    else:
        await call.message.edit_text("❌ Qaysi kanalni o‘chiramiz?", reply_markup=kb_delete_channels(channels))

    await call.answer("✅ O‘chirildi", show_alert=True)


@group_router.callback_query(F.data == "sc:close")
async def sc_close(call: CallbackQuery):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.answer()


# =========================
#   ADMIN COMMANDS
# =========================
@group_router.message(AdminOnly(), Command("help"))
async def help_group(message: Message):
    await message.answer("📌 Bot buyruqlari (FAQAT ADMIN):", reply_markup=kb_help_group())


@group_router.message(AdminOnly(), Command("mymembers"))
async def cmd_mymembers(message: Message, db: DB):
    n = await db.get_added(message.chat.id, message.from_user.id)
    await message.reply(f"📊 Siz qo‘shgan odamlar soni: <b>{n}</b>")


@group_router.message(AdminOnly(), Command("yourmembers"))
async def cmd_yourmembers(message: Message, db: DB):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("❗ Odamga reply qilib /yourmembers yozing.")
    uid = message.reply_to_message.from_user.id
    n = await db.get_added(message.chat.id, uid)
    await message.reply(f"📈 U odam qo‘shganlar soni: <b>{n}</b>")


@group_router.message(AdminOnly(), Command("top"))
async def cmd_top(message: Message, db: DB):
    rows = await db.top10(message.chat.id)
    if not rows:
        return await message.reply("Hali statistika yo‘q.")
    lines = ["🏆 Eng ko‘p odam qo‘shgan TOP 10:"]
    for i, (uid, cnt) in enumerate(rows, 1):
        lines.append(f"{i}. <a href='tg://user?id={uid}'>User</a> — <b>{cnt}</b>")
    await message.reply("\n".join(lines))


@group_router.message(AdminOnly(), Command("delson"))
async def cmd_delson(message: Message, db: DB):
    await db.reset_all_added(message.chat.id)
    await message.reply("🧹 Guruh statistikasi tozalandi!")


@group_router.message(AdminOnly(), Command("clean"))
async def cmd_clean(message: Message, db: DB):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("❗ Odamga reply qilib /clean yozing.")
    uid = message.reply_to_message.from_user.id
    await db.reset_added_for(message.chat.id, uid)
    await message.reply("🧽 Reply qilingan odam ma’lumoti 0 ga tushirildi!")


@group_router.message(AdminOnly(), Command("deforce"))
async def cmd_deforce(message: Message, db: DB):
    await db.set_required_adds(message.chat.id, 1)
    await db.set_force_text(message.chat.id, "Guruhda yozish uchun avval odam qo‘shing!")
    await db.set_force_text_delete_after(message.chat.id, 0)
    await message.reply("🧼 Majburiy sozlamalar default holatga qaytdi!")


@group_router.message(AdminOnly(), Command("add"))
async def add_menu(message: Message):
    await message.reply("👥 Guruhda odam qo‘shishni qancha qilib belgilay?", reply_markup=kb_add_required_buttons())


@group_router.message(AdminOnly(), Command("set"))
async def set_menu(message: Message, db: DB):
    s = await db.get_settings(message.chat.id)
    await message.reply(
        f"⚙️ Sozlamalar:\n"
        f"• Talab: <b>{s['required_adds']}</b> ta\n"
        f"• Matn o‘chish: <b>{s['force_text_delete_after']}</b> s\n\n"
        f"Quyidan tanlang:",
        reply_markup=kb_set_menu(),
    )


@group_router.message(AdminOnly(), Command("textforce"))
async def textforce_start(message: Message, state: FSMContext):
    await state.set_state(ForceTextState.waiting_text)
    await message.reply("✍️ Yangi majburiy matnni yuboring:", reply_markup=kb_cancel())


@group_router.message(AdminOnly(), ForceTextState.waiting_text)
async def textforce_save(message: Message, state: FSMContext, db: DB):
    txt = (message.text or "").strip()
    if not txt:
        return await message.reply("❗ Matn bo‘sh bo‘lmasin.")
    await db.set_force_text(message.chat.id, txt)
    await state.clear()
    await message.reply("✅ Saqlandi.")


@group_router.message(AdminOnly(), Command("text_time"))
async def text_time_menu(message: Message, db: DB):
    s = await db.get_settings(message.chat.id)
    await message.reply(
        "Matn avtomatik o‘chish vaqti:",
        reply_markup=kb_text_delete_time(selected_seconds=s["force_text_delete_after"]),
    )


@group_router.callback_query(F.data.startswith("txttime:"))
async def cb_text_time(call: CallbackQuery, db: DB):
    if not await cb_is_admin(call):
        return await call.answer("admin", show_alert=True)

    data = call.data.split(":")[1]
    if data == "cancel":
        await call.answer("Yopildi")
        try:
            await call.message.delete()
        except Exception:
            pass
        return

    sec = int(data)
    await db.set_force_text_delete_after(call.message.chat.id, sec)
    await call.answer("✅ Saqlandi", show_alert=True)

    try:
        await call.message.edit_reply_markup(reply_markup=kb_text_delete_time(selected_seconds=sec))
    except Exception:
        pass


@group_router.message(AdminOnly(), Command("unlink"))
async def unlink_menu(message: Message, db: DB):
    channels = await db.get_channels(message.chat.id)
    if not channels:
        return await message.reply("🔗 Ulangan kanal yo‘q.")
    await message.reply("🔗 Qaysi kanalni o‘chirmoqchisiz?", reply_markup=kb_unlink_channels(channels))


@group_router.callback_query(F.data.startswith("unlink:"))
async def cb_unlink(call: CallbackQuery, db: DB):
    if not await cb_is_admin(call):
        return await call.answer("admin", show_alert=True)

    data = call.data.split(":")[1]
    if data == "cancel":
        await call.answer("Yopildi")
        try:
            await call.message.delete()
        except Exception:
            pass
        return

    await db.remove_channel(call.message.chat.id, data)
    await call.answer(f"@{data} o‘chirildi ✅", show_alert=True)

    channels = await db.get_channels(call.message.chat.id)
    if channels:
        await call.message.edit_reply_markup(reply_markup=kb_unlink_channels(channels))
    else:
        try:
            await call.message.edit_text("🔗 Hamma kanallar o‘chirildi.")
        except Exception:
            pass


@group_router.callback_query(F.data.startswith("addreq:"))
async def cb_add_required(call: CallbackQuery, db: DB):
    if not await cb_is_admin(call):
        return await call.answer("admin", show_alert=True)

    data = call.data.split(":")[1]
    if data == "cancel":
        await call.answer("Yopildi")
        try:
            await call.message.delete()
        except Exception:
            pass
        return

    n = int(data)
    await db.set_required_adds(call.message.chat.id, n)
    await call.answer(f"✅ Talab {n} ta bo‘ldi", show_alert=True)


# =========================
#   STATISTIKA: yangi odam qo‘shilganda (REAL TIME UPDATE)
# =========================
@group_router.message(F.new_chat_members)
async def on_new_members(message: Message, db: DB):
    chat_id = message.chat.id
    inviter = message.from_user
    if not inviter:
        return
    inviter_id = inviter.id

    # bot o'zi qo'shilsa sanamaslik ixtiyoriy:
    # for m in message.new_chat_members:
    #     if m.is_bot:
    #         return

    await db.inc_added(chat_id, inviter_id, len(message.new_chat_members))

    # Agar ogohlantirish xabari bor bo'lsa, uni edit qilib yangilaymiz
    warn_id = _last_warn_msg.get((chat_id, inviter_id))
    if not warn_id:
        return

    settings = await db.get_settings(chat_id)
    required = int(settings.get("required_adds", 1))
    added = await db.get_added(chat_id, inviter_id)

    text = (
        "✅ <b>Hisob yangilandi!</b>\n\n"
        f"📌 Kerak: <b>{required}</b>\n"
        f"📊 Hozir: <b>{added}/{required}</b>\n"
        f"⏳ Qoldi: <b>{max(required - added, 0)}</b> ta"
    )

    try:
        await message.bot.edit_message_text(
            chat_id=chat_id,
            message_id=warn_id,
            text=text,
            parse_mode="HTML",
            reply_markup=kb_progress(added, required),
        )
    except Exception:
        _last_warn_msg.pop((chat_id, inviter_id), None)


# =========================
#   GUARD: odam qo‘shish + kanal a’zoligi
# =========================
@group_router.message(F.text & ~F.text.startswith("/"))
async def guard_text(message: Message, db: DB):
    if not message.from_user:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    if await AdminOnly()(message):
        return

    if await db.is_priv(chat_id, user_id):
        return

    settings = await db.get_settings(chat_id)
    required = int(settings.get("required_adds", 1))
    delete_after = int(settings.get("force_text_delete_after", 0))

    user_link = f"<a href='tg://user?id={user_id}'>{message.from_user.full_name}</a>"

    # 1) Kanal a’zoligi tekshiruvi
    channels = await db.get_channels(chat_id)
    if channels:
        ok = await is_subscribed_all(message.bot, user_id, channels)
        if not ok:
            try:
                await message.delete()
            except Exception:
                pass

            warn = await message.bot.send_message(
                chat_id=chat_id,
                text=f"❌ {user_link}, avval kanal(lar)ga a'zo bo‘ling:",
                parse_mode="HTML",
                reply_markup=kb_join_channels(channels),
            )

            if delete_after > 0:
                async def _del():
                    await asyncio.sleep(delete_after)
                    try:
                        await warn.delete()
                    except Exception:
                        pass
                asyncio.create_task(_del())
            return

    # 2) Odam qo‘shish talabi
    added = await db.get_added(chat_id, user_id)
    if required > 0 and added < required:
        try:
            await message.delete()
        except Exception:
            pass

        text = (
            "❌ <b>Siz hali odam qo‘shmagansiz!</b>\n\n"
            f"📌 Guruhda yozish uchun avval <b>{required} ta</b> odam qo‘shing.\n"
            f"📊 Hozir: <b>{added}/{required}</b>\n"
            f"⏳ Qoldi: <b>{max(required - added, 0)}</b> ta\n\n"
            f"👤 {user_link}"
        )

        msg = await message.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=kb_progress(added, required),
        )

        _last_warn_msg[(chat_id, user_id)] = msg.message_id

        if delete_after > 0:
            async def _del():
                await asyncio.sleep(delete_after)
                try:
                    await msg.delete()
                except Exception:
                    pass
            asyncio.create_task(_del())

        return


# =========================
#   CALLBACK: SUB CHECK
# =========================
@group_router.callback_query(F.data == "check_sub")
async def cb_check_sub(call: CallbackQuery, db: DB):
    if not call.message:
        return

    channels = await db.get_channels(call.message.chat.id)
    if not channels:
        return await call.answer("Kanal sozlanmagan.", show_alert=True)

    ok = await is_subscribed_all(call.bot, call.from_user.id, channels)
    await call.answer("✅ A'zo bo‘lgansiz!" if ok else "❌ Hali a'zo emassiz.", show_alert=True)


# =========================
#   CALLBACK: ADDED CHECK
# =========================
@group_router.callback_query(F.data == "check_added")
async def cb_check_added(call: CallbackQuery, db: DB):
    if not call.message:
        return

    chat_id = call.message.chat.id
    user_id = call.from_user.id

    settings = await db.get_settings(chat_id)
    required = int(settings.get("required_adds", 1))
    added = await db.get_added(chat_id, user_id)

    text = (
        "📊 <b>Tekshiruv:</b>\n\n"
        f"📌 Kerak: <b>{required}</b>\n"
        f"👤 Siz: <b>{added}/{required}</b>\n"
        f"⏳ Qoldi: <b>{max(required - added, 0)}</b> ta"
    )

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb_progress(added, required))
    await call.answer("Yangilandi ✅")


@group_router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    await call.answer("⏳ Hisob tugma orqali yangilanadi", show_alert=False)


# =========================
#   NON-ADMIN: admin komandalarini ishlatsa "admin" desin
# =========================
ADMIN_COMMANDS = {
    "help", "mymembers", "yourmembers", "top", "delson", "clean", "add",
    "textforce", "text_time", "deforce", "priv", "privs", "set", "unlink", "setchannel"
}


@group_router.message(F.text.startswith("/"))
async def non_admin_commands_reply(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return
    if not message.from_user:
        return
    if await AdminOnly()(message):
        return

    cmd = (message.text or "").split()[0].lstrip("/").split("@")[0]
    if cmd in ADMIN_COMMANDS:
        await message.reply("admin")
