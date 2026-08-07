import asyncio
import datetime
import os
from telegram import InputMediaPhoto, InputMediaVideo, InputMediaDocument
from telegram.error import RetryAfter, BadRequest, TimedOut
from telegram import LinkPreviewOptions
from telegram.error import BadRequest

MEDIA_FALLBACK_ERRORS = (
    "webpage_media_empty",
    "webpage_curl_failed",
)

BASE_URL = "https://2ch.org"

async def safe_send(func, *args, **kwargs):
    """Send with automatic flood control retry."""
    while True:
        try:
            return await func(*args, **kwargs)
        except RetryAfter as e:
            print(f"Rate limited. Sleeping {e.retry_after}s...")
            await asyncio.sleep(e.retry_after)
        except BadRequest as e:
            if any(err in str(e) for err in MEDIA_FALLBACK_ERRORS):
                raise  # Let caller handle this
            print(f"BadRequest: {e}")
            raise
        except TimedOut:
            print("Timed Out")
            continue

async def publish_post(app,chat_id,post,text):
    files = post.get('files') or []
    timestamp = datetime.datetime.fromtimestamp(int
    (post['timestamp'])).strftime('%Y-%m-%d %H:%M:%S')
    if files:
        telegram_text = f"{timestamp} | №{post['num']} | {post.get('number')}\n\n{text[:900]}"
        try:
            all_links = []
            if len(files) > 10:
                    first_group = await safe_send(send_2ch_media_group,app,
                                                   chat_id,files[:10],
                                                   caption=None
                                                   )
                    all_links.extend(msg.link for msg in first_group)
                    telegram_group = await safe_send(send_2ch_media_group,app,
                                                   chat_id,files[10:],
                                                   caption=telegram_text,
                                                   reply_to_message_id=first_group[0].message_id,
                                                   )
                    all_links.extend(msg.link for msg in telegram_group)
            else:
                telegram_group = await safe_send(send_2ch_media_group,app,
                                               chat_id,files[:10],
                                               caption=telegram_text
                                               )
                all_links.extend(msg.link for msg in telegram_group)
            return telegram_group, all_links, telegram_text
        except BadRequest as e:
            if any(err in str(e) for err in MEDIA_FALLBACK_ERRORS):
                fallback_sent = await publish_fallback_post(app,chat_id,telegram_text,files,e)
                return fallback_sent, [fallback_sent[0].link], telegram_text
            else:
                raise
    else:
        telegram_text = f"{timestamp} | №{post['num']} | {post.get('number')}\n\n{text[:3500]}"
        message_sent= await safe_send(app.bot.send_message,
                                      chat_id=chat_id,
                                      text=telegram_text,link_preview_options=
                                      LinkPreviewOptions(is_disabled=True))
        return message_sent, [message_sent.link], telegram_text




async def publish_fallback_post(app,chat_id,telegram_message,files,error):
    links = "\n".join(f"https://2ch.org{f['path']}" for f in files)
    fallback_message = f"{telegram_message}\n\nError: {str(error)}\n\nFailed to load media:\n\n{links}"
    fallback_sent = await safe_send(app.bot.send_message,
    chat_id=chat_id,
    link_preview_options=LinkPreviewOptions
    (url=f"https://2ch.org{files[0]['path']}",
     is_disabled=False
     ),text=fallback_message)
    return [fallback_sent]

async def update_reply_links(app, chat_id, reply, message_data, reply_link):
    # Guard: original post not in our data (before start_post or not sent yet)
    if reply not in message_data:
        print(f"Reply target {reply} not tracked yet, skipping edit")
        return None
    
    tg_message_id = message_data[reply]["tg_message_id"]
    message_to_reply = message_data[reply]["text"]
    edited_message = f"{message_to_reply}\n\n{reply_link}"
    
    # Guard: caption/text length limits
    limit = 1024 if message_data[reply]['type'] == 'Media' else 4096
    if len(edited_message) > limit:
        edited_message = edited_message[:limit - 20] + "\n\n... (truncated)"
    
    try:
        if message_data[reply]['type'] == 'Media':
            await safe_send(
                app.bot.edit_message_caption,
                chat_id=chat_id,
                message_id=tg_message_id,
                caption=edited_message,
            )
        else:
            await safe_send(
                app.bot.edit_message_text,
                chat_id=chat_id,
                message_id=tg_message_id,
                text=edited_message,
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )
        return edited_message
    except Exception as e:
        print(f"Failed to edit reply {reply}: {e}")
        return None

#async def update_reply_links(app,chat_id,reply,message_data,reply_link,):
#    tg_message_id = message_data[reply]["tg_message_id"]
#    message_to_reply = message_data[reply]["text"]
#    edited_message = f"{message_to_reply}\n\n{reply_link}" 
#    if message_data[reply]['type'] == 'Media':
#        await safe_send(
#                       app.bot.edit_message_caption,
#                       chat_id=chat_id,
#                       message_id=tg_message_id,
#                       caption=edited_message,
#                       )
#    else:
#        await safe_send(
#                       app.bot.edit_message_text,
#                       chat_id=chat_id,
#                       message_id=tg_message_id,
#                       text=edited_message,
#                       link_preview_options=
#                       LinkPreviewOptions(is_disabled=True)
#                       )
#    return edited_message

async def pin_OP(app,chat_id,message_id):
    await safe_send(
        app.bot.pin_chat_message,
        chat_id=chat_id,
        message_id=message_id,
    )

async def send_2ch_media_group(app, chat_id,  files, reply_to_message_id=None, caption=None,):
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
    
    return await app.bot.send_media_group(chat_id=chat_id, media=media,reply_to_message_id=reply_to_message_id)


