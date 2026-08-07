import asyncio
from telegram.ext import ApplicationBuilder
from state import load_state, save_state,remember_post, remember_links
import board_service
from telegram_service import update_reply_links, pin_OP,publish_post
from config import BOT_TOKEN, CHAT_ID, BOARD, THREAD_ID, FIRST_LOOP_DELAY, LOOP_DELAY, POLL_INTERVAL

chat_id = CHAT_ID
bot_token = BOT_TOKEN
board = BOARD
thread_id = THREAD_ID

async def monitor_2ch(app):
    seen_posts, post_map, message_data, saved_start = load_state()
    current_start = app.bot_data["start_post"]
    is_first_loop = len(seen_posts) == 0  # only true if nothing was ever sent

    while True:
        data = await asyncio.to_thread(board_service.get_thread, board, thread_id)
        posts = data['threads'][0]['posts']

        for post in posts:
            post_num = post['num']

            # Skip silently — don't pollute seen_posts
            if post['number'] < current_start:
                continue

            # Already sent — skip
            if post_num in seen_posts:
                continue
            has_replies = False
            text = board_service.clean_comment(post.get('comment', ''))
            text,has_replies,reply_nums = board_service.linkify_replies(text, post_map)
            message_sent, all_links, telegram_text = await publish_post(app,chat_id,post,text)
            files = post.get('files') or []
            if files:
                message_id = message_sent[0].message_id
                msg_type = "Media"
            else:
                message_id = message_sent.message_id
                msg_type = "Text"

            remember_post(post,message_sent,message_data,telegram_text,message_id,msg_type)
            remember_links(post_map,post,all_links)

            if has_replies:
                for reply in reply_nums:
                    message_data[reply]['text'] = await update_reply_links(app,chat_id,reply,message_data,all_links[0])

            print(telegram_text)
            print()
            if post.get('files'):
                for f in post['files']:
                    print(f"📎https://2ch.org{f['path']}")
            print()
            if post.get('number') == 1:
                await pin_OP(app,chat_id,message_sent[0].message_id)
            seen_posts.add(post_num)
            save_state(seen_posts,post_map,message_data,start_post)
            await asyncio.sleep(FIRST_LOOP_DELAY if is_first_loop else LOOP_DELAY)


        is_first_loop = False
        await asyncio.sleep(POLL_INTERVAL)


async def on_start(app):
    asyncio.create_task(monitor_2ch(app))
start_post = int(
    input(f"Select start post (0-{board_service.get_thread(board, thread_id)['posts_count']}, 0 = all): ")
)

app = ApplicationBuilder().token(bot_token).post_init(on_start).build()

app.bot_data["start_post"] = start_post
app.run_polling()
