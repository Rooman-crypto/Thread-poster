import asyncio
import board_service
from state import update_config_thread_id


async def send_startup_message(app, chat_id, board, thread_id):
    await app.bot.send_message(
        chat_id=chat_id,
        text=f"Select start post (0-{board_service.get_thread(board, thread_id)['posts_count']}, 0 = all): "
    )


async def backfill(update, context):
    app = context.application

    start_post = int(context.args[0])
    app.bot_data["start_post"] = start_post
    app.bot_data["start_event"].set()

    await update.message.reply_text(
        f"Starting from post {start_post}"
    )


async def get_id(update, context):
    print(update.effective_chat.id)
    await update.message.reply_text(
        f"Your chat ID is {update.effective_chat.id}"
    )


async def switch_thread(update, context):
    app = context.application

    candidates = app.bot_data.get("thread_candidates", [])

    if not candidates:
        await update.message.reply_text(
            "There are no pending thread candidates."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /switch <number>"
        )
        return
    try:
        index = int(context.args[0]) - 1
    except ValueError:
        await update.message.reply_text(
            "The candidate number must be an integer."
        )
        return
    if index < 0 or index >= len(candidates):
        await update.message.reply_text(
            "That candidate does not exist."
        )
        return

    selected_thread = candidates[index]
    app.bot_data["thread_id"] = selected_thread
    app.bot_data["start_post"] = 1
    app.bot_data["thread_candidates"] = []
    app.bot_data["candidate_message_id"] = None
    print("SWITCHED TO:", app.bot_data["thread_id"])

    update_config_thread_id(selected_thread)

    app.bot_data["thread_switch_event"].set()
    await update.message.reply_text(
        f"Switched to thread {selected_thread}."
    )


async def update_thread_candidates(app, chat_id, candidates):
    if not candidates:
        return
    current_candidates = app.bot_data.setdefault("thread_candidates", [])
    changed = False
    for candidate in candidates:
        if candidate not in current_candidates:
            current_candidates.append(candidate)
            changed = True
    
    if not changed:
        return

    if not current_candidates:
        return

    message = "Found possible next threads:\n\n"

    for i, candidate in enumerate(current_candidates, 1):
        message += f"{i}. {candidate}\n"

    message += "\nUse /switch <number> to switch."

    message_id = app.bot_data.get("candidate_message_id")

    if message_id is None:
        sent = await app.bot.send_message(
            chat_id=chat_id,
            text=message,
        )
        app.bot_data["candidate_message_id"] = sent.message_id

    else:
        await app.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=message,
        )
