import os
from telegram import InputMediaPhoto, InputMediaVideo, InputMediaDocument

BASE_URL = "https://2ch.org"

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

