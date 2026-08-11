import asyncio

from telegram.ext import ApplicationBuilder, CommandHandler

from state import *
import board_service

from telegram_service import (
    update_reply_links,
    pin_OP,
    publish_post,
)

from config import *
from bot_service import *


chat_id = CHAT_ID
bot_token = BOT_TOKEN
board = BOARD


async def monitor_2ch(app):
    # Wait for the first /start command.
    await app.bot_data["start_event"].wait()

    seen_posts, post_map, message_data, saved_start = load_state()

    last_thread_id = None
    is_first_loop = True

    while True:
        thread_id = app.bot_data["thread_id"]

        # Detect a thread change.
        if thread_id != last_thread_id:
            seen_posts, post_map, message_data, saved_start = load_state()

            current_start = app.bot_data.get("start_post")

            if current_start is None:
                current_start = (
                    saved_start
                    if saved_start is not None
                    else 1
                )

            is_first_loop = True
            last_thread_id = thread_id

            print(
                f"Thread changed to {thread_id}, "
                f"start={current_start}"
            )

        else:
            current_start = app.bot_data.get("start_post")

            if current_start is None:
                current_start = (
                    saved_start
                    if saved_start is not None
                    else 1
                )

        # Capture whether this pass is a /start pass.
        #
        # During a /start pass, already-seen posts are deliberately
        # published again.
        start_requested = app.bot_data.get(
            "start_requested",
            False,
        )

        #print(
        #    "MONITOR USING:",
        #    thread_id,
        #    "START:",
        #    current_start,
        #    "REPUBLISH:",
        #    start_requested,
        #)

        data = await asyncio.to_thread(
            board_service.get_thread,
            BOARD,
            thread_id,
        )

        posts = data["threads"][0]["posts"]

        for post in posts:
            # /switch may have happened while we were processing
            # the previous post.
            if thread_id != app.bot_data["thread_id"]:
                break

            post_num = str(post["num"])
            post_number = post["number"]

            # Ignore everything before the requested start.
            if post_number < current_start:
                continue

            # During /start, deliberately ignore seen_posts.
            #
            # During normal monitoring, skip already-published posts.
            if post_num in seen_posts and not start_requested:
                continue

            text = board_service.clean_comment(
                post.get("comment", "")
            )

            text, reply_nums = (
                board_service.linkify_replies(
                    text,
                    post_map,
                )
            )

            published = await publish_post(
                app,
                chat_id,
                post,
                text,
            )

            # Only mark the post as seen after successful publishing.
            seen_posts.add(post_num)

            files = post.get("files") or []

            remember_post(
                post,
                message_data,
                published,
            )

            remember_links(
                post_map,
                post_num,
                published.links,
            )

            if reply_nums:
                for reply in reply_nums:
                    replied_text = await update_reply_links(
                        app,
                        chat_id,
                        reply,
                        message_data,
                        published.links[0],
                        post_num,
                    )

                    if replied_text is not None:
                        update_replied_message(
                            message_data,
                            reply,
                            replied_text,
                        )

            print(published.text)
            print()

            if files:
                for f in files:
                    print(
                        f"📎https://2ch.org{f['path']}"
                    )

            print()

            if post_number == 1:
                await asyncio.sleep(1.8)

                await pin_OP(
                    app,
                    chat_id,
                    published.message_id,
                )

            save_state(
                seen_posts,
                post_map,
                message_data,
                current_start,
            )

            # Search for possible next threads.
            if post_number >= 480:
                switch_candidates = (
                    board_service.extract_new_thread_candidates(
                        published.text,
                        thread_id,
                    )
                )

                if switch_candidates:
                    await update_thread_candidates(
                        app,
                        OWNER_CHAT_ID,
                        switch_candidates,
                    )

            # Check for a thread switch after publishing.
            if thread_id != app.bot_data["thread_id"]:
                break

            # If a command arrives, wake immediately instead of
            # waiting through the normal delay.
            try:
                await asyncio.wait_for(
                    app.bot_data["control_event"].wait(),
                    timeout=(
                        FIRST_LOOP_DELAY
                        if is_first_loop
                        else LOOP_DELAY
                    ),
                )
            except asyncio.TimeoutError:
                pass
            else:
                app.bot_data["control_event"].clear()
                break

        # The /start pass is finished once we reached the current
        # end of the fetched post list.
        if start_requested:
            app.bot_data["start_requested"] = False
            print("START PASS FINISHED")

        is_first_loop = False

        # A switch happened. Immediately start another iteration
        # using the new thread.
        if thread_id != app.bot_data["thread_id"]:
            continue

        # Wait for normal polling or a command.
        try:
            await asyncio.wait_for(
                app.bot_data["control_event"].wait(),
                timeout=POLL_INTERVAL,
            )
        except asyncio.TimeoutError:
            pass
        else:
            app.bot_data["control_event"].clear()


async def on_start(app):
    app.bot_data["thread_id"] = THREAD_ID

    # Initial value. /start will replace it.
    app.bot_data["start_post"] = None

    # Prevent monitor from starting until the first /start.
    app.bot_data["start_event"] = asyncio.Event()

    # Used to wake monitor when /start or /switch happens.
    app.bot_data["control_event"] = asyncio.Event()

    # True only while processing a /start request.
    app.bot_data["start_requested"] = False

    app.bot_data["thread_candidates"] = []
    app.bot_data["candidate_message_id"] = None

    await send_startup_message(
        app,
        OWNER_CHAT_ID,
        BOARD,
        app.bot_data["thread_id"],
    )

    asyncio.create_task(
        monitor_2ch(app)
    )


app = (
    ApplicationBuilder()
    .token(bot_token)
    .post_init(on_start)
    .build()
)

app.add_handler(
    CommandHandler("start", start)
)

app.add_handler(
    CommandHandler("id", get_id)
)

app.add_handler(
    CommandHandler("switch", switch_thread)
)

app.run_polling()
