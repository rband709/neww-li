from telethon import events,functions,errors
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from config import Config
import asyncio
import threading
import requests
import re

def cronjob():
    threading.Timer(60*5, cronjob).start()
    requests.get(Config.DOMAIN)
    
cronjob()

client = TelegramClient(
            StringSession(),
            Config.API_ID,
            Config.API_HASH,
            # proxy=("socks5","127.0.0.1",9050)
            ).start(bot_token=Config.TOKEN)

username_bot = client.get_me().username

def get_file_name(message):
    if message.file.name:
        return message.file.name.replace(" ","-")
    ext = message.file.ext or ""
    return f"file{ext}"

@client.on(events.NewMessage)
async def download(event):
    if (pv := event.is_private) or event.is_group :
        if pv:
            try:
                await event.client(functions.channels.GetParticipantRequest(
                    channel = Config.CHANNEL_USERNAME,
                    participant = event.sender_id
                    ))
            except errors.UserNotParticipantError:
                await event.reply(f"ابتدا در کانال زیر عضو شوید سپس فایل خود را ارسال نمایید.↙️\n\n@{Config.CHANNEL_USERNAME}\n\n⭕️بعد از عضو شدن /start کلیک کنید.")
                return
        
        if event.file :
            if not pv :
                if not event.file.size > 10_000_000:
                    return 
            sender = await event.get_sender()
            msg = await event.client.send_file(
                Config.CHANNEL,
                file=event.message.media,
                caption=f"@{sender.username}|[{event.chat_id}](tg://user?id={event.sender_id})/{event.message.id}")
            id_hex = hex(msg.id)[2:]
            id = f"{id_hex}/{get_file_name(msg)}"
            bot_url = f"t.me/{username_bot}?start={id_hex}"
            await event.reply(f"⚡ لینک اشتراک گذاری فایل شما 👇: \n📎 : {bot_url}")
            return

        elif id_msg := re.search("/start (.*)", event.raw_text ):
            if id_hex := id_msg.group(1) :
                try:
                    id = int(id_hex,16)
                except ValueError:
                    return
                msg = await event.client.get_messages(Config.CHANNEL,ids=id)
                if not msg or not msg.file :
                    return await event.reply("404! File Not Found")
                if regex := re.search(r"(\d*)/(\d*)",msg.message):
                    if user_id := int(regex.group(1)) :
                        msg_id = int(regex.group(2))
                        file = await event.client.get_messages(user_id,ids=msg_id)
                        if not file or not file.file :
                            return await event.reply("404! File Not Found")
                        forward = await file.forward_to(event.chat_id)
                        id_name = f"{id_hex}/{get_file_name(msg)}"
                        bot_url = f"t.me/{username_bot}?start={id_hex}"
                        forward_reply = await forward.reply(f"فایل بعد از 21 ثانیه دیگر حذف میشود 🔔")
                        await asyncio.sleep(12)
                        await forward_reply.edit(f"🔔 فایل بعد از 9 ثانیه دیگر حذف میشود.")
                        await asyncio.sleep(10)
                        await forward.delete()
                        await forward_reply.edit(f"✅ دریافت دوباره فایل 👇/n 🤖 : {bot_url}",link_preview=True)
                return
        if pv:
            await event.reply("👋 سلام ، من ربات دریافت فایل های کانال سریزپلاس هستم /n جهت دریافت فایل لینک درج شده در کانال را کلیک کنید به ربات هدایت میشود بعد start را کلیک کنید ، فایل برایتان ارسال میشود.⁦❤️⁩ ")
        

    elif event.is_channel:
        if event.chat_id == Config.CHANNEL:
            if event.reply_to:
                msg = await event.get_reply_message()
                if regex := re.search(r"(\d*)/(\d*)",msg.message):
                    if user_id := int(regex.group(1)) :
                        msg_id = int(regex.group(2))
                        if await event.client.send_message(entity=user_id, message=event.message, reply_to=msg_id):
                            await event.client.edit_message(event.chat_id,event.id,f"{event.message.message}\n sended")
                        
                        
                    
client.run_until_disconnected()
