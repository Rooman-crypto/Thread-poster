import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler
from state import *
import board_service
from telegram_service import update_reply_links, pin_OP, publish_post
from config import *
from bot_service import *

chat_id = CHAT_ID
bot_token = BOT_TOKEN
board = BOARD
thread_id = THREAD_ID


async def monitor_2ch(app):
    await app.bot_data["start_event"].wait()
    seen_posts, post_map, message_data, saved_start = load_state()
    switch_candidates = []
    last_thread_id = None

    while True:
        print("MONITOR USING:", app.bot_data["thread_id"])
        thread_id = app.bot_data["thread_id"]

        # Reset thread-local filter state on every thread change
        if thread_id != last_thread_id:
            start_post = app.bot_data.get("start_post")
            if start_post is None:
                current_start = saved_start if saved_start is not None else 1
            else:
                current_start = start_post
            is_first_loop = True
            last_thread_id = thread_id
            print(f"Thread changed to {thread_id}, start={current_start}")

        data = await asyncio.to_thread(
            board_service.get_thread,
            BOARD,
            thread_id,
        )
        posts = data['threads'][0]['posts']

        for post in posts:
            if thread_id != app.bot_data["thread_id"]:
                break
            print(post)
            post_num = str(post['num'])
            post_number = post['number']

            if post['number'] < current_start:
                continue

            if post_num in seen_posts:
                continue
            seen_posts.add(post_num)

            text = board_service.clean_comment(post.get('comment', ''))
            text, has_replies, reply_nums = board_service.linkify_replies(text, post_map)
            published = await publish_post(app, chat_id, post, text)
            files = post.get('files') or []
            remember_post(post, message_data, published)
            remember_links(post_map, post_num, published.links)

            if reply_nums:
                for reply in reply_nums:
                    replied_text = await update_reply_links(app, chat_id, reply, message_data, published.links[0])
                    update_replied_message(message_data, reply, replied_text)

            print(published.text)
            print()
            if files:
                for f in post['files']:
                    print(f"📎https://2ch.org{f['path']}")
            print()
            if post_number == 1:
                await asyncio.sleep(1.8)
                await pin_OP(app, chat_id, published.message_id)
            save_state(seen_posts, post_map, message_data, current_start)
            await asyncio.sleep(FIRST_LOOP_DELAY if is_first_loop else LOOP_DELAY)
            if post_number >= 480:
                switch_candidates = board_service.extract_new_thread_candidates(
                    published.text,
                    thread_id,
                )
                if switch_candidates:
                    await update_thread_candidates(
                        app,
                        OWNER_CHAT_ID,
                        switch_candidates,
                    )
        is_first_loop = False
        try:
            await asyncio.wait_for(
                app.bot_data["thread_switch_event"].wait(),
                timeout=POLL_INTERVAL,
            )
        except asyncio.TimeoutError:
            pass
        else:
            app.bot_data["thread_switch_event"].clear()


async def on_start(app):
    app.bot_data["thread_id"] = THREAD_ID
    app.bot_data["start_post"] = None
    app.bot_data["start_event"] = asyncio.Event()
    app.bot_data["thread_candidates"] = []
    app.bot_data["candidate_message_id"] = None
    app.bot_data["thread_switch_event"] = asyncio.Event()

    await send_startup_message(
        app,
        OWNER_CHAT_ID,
        BOARD,
        app.bot_data["thread_id"],
    )

    asyncio.create_task(monitor_2ch(app))

app = ApplicationBuilder().token(bot_token).post_init(on_start).build()
app.add_handler(CommandHandler("backfill", backfill))
app.add_handler(CommandHandler("id", get_id))
app.add_handler(CommandHandler("switch", switch_thread))
app.run_polling()
