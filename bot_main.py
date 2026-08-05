import requests
import asyncio
from telegram.ext import ApplicationBuilder

import main  # your 2ch code

chat_id =   
bot_token = 


async def monitor_2ch(app):
    """New: fetch 2ch thread and post new comments"""
    board = 'fag'
    thread_id = 27563266
    seen_posts = set()
    while True:
        # Fetch thread (sync function, run in thread pool)
        data = await asyncio.to_thread(main.get_thread, board, thread_id)
        posts = data['threads'][0]['posts']
        for post in posts:
            post_num = post['num']
            if post_num not in seen_posts:
                seen_posts.add(post_num)
                text = main.clean_comment(post.get('comment', ''))
                if text:
                    message = f"{post.get('number')} | #{post_num} | ts:{post.get('timestamp')}\n\n{text[:3500]}"
                    await app.bot.send_message(
                        chat_id=chat_id, 
                        text=message
                    )
        await asyncio.sleep(30)

async def on_start(app):
    asyncio.create_task(monitor_2ch(app))       # new 2ch monitor

app = ApplicationBuilder().token(bot_token).post_init(on_start).build()
app.run_polling()
