import os
from telegram import InputMediaPhoto, InputMediaVideo, InputMediaDocument
from telegram.error import BadRequest

BASE_URL = "https://2ch.org"

async def send_2ch_media_group(app, chat_id, files, caption=None):
    media = []
    
    for i, f in enumerate(files[:10]):
        ext = os.path.splitext(f.get('name', ''))[1].lower()
        url = BASE_URL + f['path']
        item_caption = caption if i == 0 else None
        
        if ext in ('.jpg', '.jpeg', '.png', '.webp', '.bmp'):
            media.append(InputMediaPhoto(media=url, caption=item_caption))
        elif ext in ('.mp4', '.mov', '.avi', '.mkv'):
            media.append(InputMediaVideo(media=url, caption=item_caption))
        else:
            media.append(InputMediaDocument(media=url, caption=item_caption))
    
    return await app.bot.send_media_group(chat_id=chat_id, media=media)


async def send_post_with_fallback(app, chat_id, files, caption, board, thread_id, post_num):
    """Try to send media group. If it fails, send text with links instead."""
    try:
        await send_2ch_media_group(app, chat_id, files[:10], caption=caption)
        if len(files) > 10:
            await send_2ch_media_group(app, chat_id, files[10:], caption=None)
        return
    except BadRequest as e:
        if "webpage_media_empty" in str(e) or "wrong file identifier" in str(e):
            # Build fallback text with links
            links = "\n".join(f"📎 https://2ch.org{f['path']}" for f in files)
            fallback = f"{caption}\n\n{links}"
            await app.bot.send_message(chat_id=chat_id, text=fallback[:4000])
        else:
            raise