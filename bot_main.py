import asyncio
import datetime
from telegram.ext import ApplicationBuilder
from telegram.error import RetryAfter, BadRequest, TimedOut
from telegram_utils import send_2ch_media_group
from telegram import LinkPreviewOptions
from state import load_state, save_state
import main

chat_id = 
bot_token = 

errors = ("webpage_media_empty","webpage_curl_failed")

async def safe_send(func, *args, **kwargs):
    """Send with automatic flood control retry."""
    while True:
        try:
            return await func(*args, **kwargs)
        except RetryAfter as e:
            print(f"Rate limited. Sleeping {e.retry_after}s...")
            await asyncio.sleep(e.retry_after)
        except BadRequest as e:
            if any(err in str(e) for err in errors):
                raise  # Let caller handle this
            print(f"BadRequest: {e}")
            raise
        except TimedOut:
            print("Timed Out")
            continue
async def send_post_message(app, chat_id, post, text, timestamp, post_map):
    message = (
        f"{timestamp} | #{post['num']} | {post.get('number')}\n\n"
        f"{text[:3500]}"
    )

    message_sent = await safe_send(
        app.bot.send_message,
        chat_id=chat_id,
        text=message,
    )

    print(message_sent.message_id)
    print(message_sent.link)

    post_map[post["num"]] = message_sent.link

    return message_sent

async def monitor_2ch(app):
    board = 'fag'
    thread_id = 27574729
    seen_posts, post_map = load_state()
    is_first_loop = len(seen_posts) == 0

    while True:
        data = await asyncio.to_thread(main.get_thread, board, thread_id)
        posts = data['threads'][0]['posts']

        for post in posts:
            post_num = post['num']

            if post_num in seen_posts:
                continue

            seen_posts.add(post_num)
            text = main.clean_comment(post.get('comment', ''))
            text = main.linkify_replies(text, post_map)
            timestamp = datetime.datetime.fromtimestamp(
                int(post['timestamp'])
            ).strftime('%Y-%m-%d %H:%M:%S')
            files = post.get('files') or []
            if files:
                link = f"https://2ch.org/{board}/res/{thread_id}.html#{post['num']}"
                caption = f"{timestamp} | #{post['num']} | {post.get('number')}\n\n{text[:900]}"
                try:
                    all_links= []
                    message_sent = await safe_send(send_2ch_media_group, app, chat_id, files[:10], caption=caption)
                    for msg in message_sent: all_links.append(msg.link)
                    if len(files) > 10:
                        message_sent = await safe_send(send_2ch_media_group, app,
                                       chat_id, files[10:],reply_to_message_id=message_sent[0].message_id,
                                        caption=None)
                        for msg in message_sent: all_links.append(msg.link)
                    post_map[post.get('num')] = all_links

                except BadRequest as e: # Errors handling
                    if any(err in str(e) for err in errors):
                        links = "\n".join(f"https://2ch.org{f['path']}" for f in files)
                        message_sent = await safe_send(app.bot.send_message, chat_id=chat_id,
                                       link_preview_options=LinkPreviewOptions(url=str(links),
                                       is_disabled=False),
                                       text=f"{caption}\n\nFailed to load media: \n\n{links}.\n\n Error: {str(e)}")
                        post_map[post.get('num')] = [message_sent.link]
                    else:
                        raise
            else:
                message = f"{timestamp} | #{post['num']} | {post.get('number')}\n\n{text[:3500]}"
                message_sent= await safe_send(app.bot.send_message, chat_id=chat_id, text=message,link_preview_options=LinkPreviewOptions(is_disabled=True))
                print(message_sent.message_id)
                print(message_sent.link)
                post_map[post.get('num')] = [message_sent.link]

            save_state(seen_posts,post_map)
            await asyncio.sleep(3 if is_first_loop else 1.5)

            print(f"{message if not files else caption}")
            print()

            if post.get('files'):
                for f in post['files']:
                    print(f"📎https://2ch.org{f['path']}")
            print()
            if post.get('number') == 1:
                await app.bot.pin_chat_message(chat_id=chat_id, message_id=message_sent[0].message_id)

        is_first_loop = False
        await asyncio.sleep(15)


async def on_start(app):
    asyncio.create_task(monitor_2ch(app))

app = ApplicationBuilder().token(bot_token).post_init(on_start).build()
app.run_polling()
