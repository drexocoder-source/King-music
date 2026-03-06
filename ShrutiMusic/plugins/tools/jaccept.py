import asyncio
from pyrogram import filters
from pyrogram.types import (
    ChatJoinRequest,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    Message
)
from pyrogram.enums import ChatMemberStatus
from ShrutiMusic import app
from ShrutiMusic.core.mongo import mongodb
from ShrutiMusic.utils.permissions import adminsOnly
from config import BANNED_USERS

approvaldb = mongodb.approval


async def approval_status(chat_id: int):
    data = await approvaldb.find_one({"chat_id": chat_id})
    if not data:
        return False
    return data.get("status", False)


async def set_approval(chat_id: int, status: bool):
    await approvaldb.update_one(
        {"chat_id": chat_id},
        {"$set": {"status": status}},
        upsert=True
    )


@app.on_message(filters.command("approval") & filters.group & ~BANNED_USERS)
@adminsOnly("can_invite_users")
async def approval_toggle(_, message: Message):

    if len(message.command) < 2:
        return await message.reply_text(
            "Usage:\n"
            "<code>/approval on</code>\n"
            "<code>/approval off</code>"
        )

    state = message.command[1].lower()

    if state == "on":
        await set_approval(message.chat.id, True)
        await message.reply_text("✅ <b>Join Request Approval Enabled.</b>")

    elif state == "off":
        await set_approval(message.chat.id, False)
        await message.reply_text("❌ <b>Join Request Approval Disabled.</b>")

    else:
        await message.reply_text("Use <code>on</code> or <code>off</code>.")


# ---------------- JOIN REQUEST EVENT ---------------- #

@app.on_chat_join_request()
async def join_request_handler(_, request: ChatJoinRequest):

    chat_id = request.chat.id

    if not await approval_status(chat_id):
        return

    user = request.from_user

    mention = user.mention
    username = f"@{user.username}" if user.username else "No Username"

    text = (
        "<b>📥 New Join Request</b>\n\n"
        f"<b>Name:</b> {mention}\n"
        f"<b>Username:</b> {username}\n"
        f"<b>User ID:</b> <code>{user.id}</code>"
    )

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Accept",
                    callback_data=f"approve_{chat_id}_{user.id}"
                ),
                InlineKeyboardButton(
                    "❌ Decline",
                    callback_data=f"decline_{chat_id}_{user.id}"
                )
            ]
        ]
    )

    await app.send_message(chat_id, text, reply_markup=buttons)


# ---------------- BUTTON HANDLER ---------------- #

@app.on_callback_query(filters.regex("approve_|decline_"))
async def approval_buttons(_, query: CallbackQuery):

    data = query.data.split("_")
    action = data[0]
    chat_id = int(data[1])
    user_id = int(data[2])

    member = await app.get_chat_member(chat_id, query.from_user.id)

    if member.status not in [
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER
    ]:
        return await query.answer("Admins only.", show_alert=True)

    if not member.privileges.can_invite_users:
        return await query.answer(
            "You need invite permission.",
            show_alert=True
        )

    if action == "approve":

        await app.approve_chat_join_request(chat_id, user_id)

        user = await app.get_users(user_id)

        await query.message.edit_text(
            f"✅ <b>Join Request Accepted</b>\n\n{user.mention} joined the group."
        )

    elif action == "decline":

        await app.decline_chat_join_request(chat_id, user_id)

        user = await app.get_users(user_id)

        await query.message.edit_text(
            f"❌ <b>Join Request Declined</b>\n\n{user.mention} request rejected."
        )

    await query.answer()
