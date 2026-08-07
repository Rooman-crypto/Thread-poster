# Image board thread poster
## Description
Telegram bot, that uses image board's thread API and posts it as a message in a Telegram channel.  
This lets user read thread, specified in a config file in a Telegram channel.
### Libraries
- python-telegram-bot
- `pip install python-telegram-bot requests`
### Bot features
- Sends Telegram message with media fetched from original
image board post.
- On fetching fail, sends fallback message.
- Keeps track of reply history.
- Edits message that was replied to, adds link of reply message to the original message.
- Pins OP post.
