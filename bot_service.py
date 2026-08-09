import board_service

from state import (
    clear_thread_state,
    load_state,
    save_state,
    update_config_thread_id,
)


async def send_startup_message(
    app,
    chat_id,
    board,
    thread_id,
):
    posts_count = board_service.get_thread(
        board,
        thread_id,
    )["posts_count"]

    await app.bot.send_message(
        chat_id=chat_id,
        text=(
            f"Select start post "
            f"(0-{posts_count}, 0 = all):"
        ),
    )


async def start(update, context):
    app = context.application

    if not context.args:
        await update.message.reply_text(
            "Usage: /start <post_number>"
        )
        return

    try:
        start_post = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "Post number must be an integer."
        )
        return

    if start_post < 0:
        await update.message.reply_text(
            "Post number cannot be negative."
        )
        return

    # Set the new lower boundary.
    app.bot_data["start_post"] = start_post

    # Tell monitor that this is a republishing pass.
    app.bot_data["start_requested"] = True

    # Keep all existing state.
    seen_posts, post_map, message_data, _ = load_state()

    save_state(
        seen_posts,
        post_map,
        message_data,
        start_post,
    )

    # Wake an already-running monitor immediately.
    app.bot_data["control_event"].set()

    # Also releases the initial startup wait.
    app.bot_data["start_event"].set()

    await update.message.reply_text(
        f"Starting from post {start_post}."
    )


async def get_id(update, context):
    print(update.effective_chat.id)

    await update.message.reply_text(
        f"Your chat ID is {update.effective_chat.id}"
    )


async def switch_thread(update, context):
    app = context.application

    candidates = app.bot_data.get(
        "thread_candidates",
        [],
    )

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

    # Change active thread.
    app.bot_data["thread_id"] = selected_thread

    # New thread starts from post 1.
    app.bot_data["start_post"] = 1

    # Do not carry a /start republishing pass into the new thread.
    app.bot_data["start_requested"] = False

    # Candidates belong to the old thread.
    app.bot_data["thread_candidates"] = []
    app.bot_data["candidate_message_id"] = None

    # Completely clear old thread tracking.
    clear_thread_state(1)

    # Persist the new thread ID.
    update_config_thread_id(selected_thread)

    print(
        "SWITCHED TO:",
        app.bot_data["thread_id"],
    )

    # Wake monitor immediately.
    app.bot_data["control_event"].set()

    await update.message.reply_text(
        f"Switched to thread {selected_thread}."
    )


async def update_thread_candidates(
    app,
    chat_id,
    candidates,
):
    if not candidates:
        return

    current_candidates = app.bot_data.setdefault(
        "thread_candidates",
        [],
    )

    changed = False

    for candidate in candidates:
        if candidate not in current_candidates:
            current_candidates.append(candidate)
            changed = True

    # No new candidates means the existing Telegram message
    # should not be edited.
    if not changed:
        return

    message = "Found possible next threads:\n\n"

    for i, candidate in enumerate(
        current_candidates,
        1,
    ):
        message += f"{i}. {candidate}\n"

    message += "\nUse /switch <number> to switch."

    message_id = app.bot_data.get(
        "candidate_message_id"
    )

    if message_id is None:
        sent = await app.bot.send_message(
            chat_id=chat_id,
            text=message,
        )

        app.bot_data["candidate_message_id"] = (
            sent.message_id
        )

    else:
        await app.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=message,
        )
