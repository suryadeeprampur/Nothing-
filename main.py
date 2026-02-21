import os
import re
import threading
from time import sleep

import pyrogram
import requests
from pymongo import MongoClient
from pyrogram import Client, enums, filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import bypasser
import ddl
from ddl import ddllist
from helpers import b64_to_str, get_current_time, shorten_url, str_to_b64
from scraper import scrapper, scrapper_sites
from texts import HELP_TEXT
from os import environ, remove


def getenv(var): return environ.get(var) or DATA.get(var, None)
# bot


API_ID = int(os.environ.get("API_ID", "27958870"))
API_HASH = os.environ.get("API_HASH", "90227e2449ed6924b95f241b0110d1e6")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8426633238:AAGTa5eTLy3jueGruhKAad2g8u8bvu8oRGg")
OWNER_ID = os.environ.get("OWNER_ID", "7404203924")
ADMIN_LIST = [int(ch) for ch in (os.environ.get("ADMIN_LIST", f"{OWNER_ID}")).split()]
OWNER_USERNAME = "RDX1444"
PERMANENT_GROUP = os.environ.get("PERMANENT_GROUP", "-1001775437494")
GROUP_ID = [int(ch) for ch in (os.environ.get("GROUP_ID", f"{PERMANENT_GROUP}")).split()]
UPDATES_CHANNEL = str(os.environ.get("UPDATES_CHANNEL", "RDX_PVT_HD"))
DB_URL = os.environ.get("DB_URL", "mongodb+srv://dhanapal:dhanapal@dhanapal.pvrwtmv.mongodb.net/?retryWrites=true&w=majority")
U_NAME = os.environ.get("BOT_USERNAME", "RDX_PVT_HD")

app = Client(
    "my_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)
# db setup
client = MongoClient(DB_URL)
db = client["mydb"]
collection = db["users"]

if collection.find_one({"role":"admin"}):
    pass
else:
    document = {"role":"admin","value":ADMIN_LIST}
    collection.insert_one(document)

if collection.find_one({"role":"auth_chat"}):
    pass
else:
    document = {"role":"auth_chat","value":GROUP_ID}
    collection.insert_one(document)

# handle ineex
def handleIndex(ele,message,msg):
    result = bypasser.scrapeIndex(ele)
    try: app.delete_messages(message.chat.id, msg.id)
    except: pass
    for page in result: app.send_message(message.chat.id, page, reply_to_message_id=message.id, disable_web_page_preview=True)


# loop thread
def loopthread(message, otherss=False):
    
    urls = []
    if otherss:
        texts = message.caption
    else:
        texts = message.text

    if texts in [None, ""]:
        return
    for ele in texts.split():
        if "http://" in ele or "https://" in ele:
            urls.append(ele)
    if len(urls) == 0:
        return
    
    uid = message.from_user.id
    if uid not in ADMIN_LIST:
        result = collection.find_one({"user_id": uid})
        if result is None:
            ad_code = str_to_b64(f"{uid}:{str(get_current_time() + 43200)}")
            ad_url = shorten_url(f"https://telegram.me/{U_NAME}?start={ad_code}")
            app.send_message(
                message.chat.id,
                f"Hey **{message.from_user.mention}** \n\nYour Ads token is expired, refresh your token and try again. \n\n**Token Timeout:** 12 hour \n\n**What is token?** \nThis is an ads token. If you pass 1 ad, you can use the bot for 12 hour after passing the ad.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Click Here To Refresh Token",
                                url=ad_url,
                            )
                        ]
                    ]
                ),
                reply_to_message_id=message.id,
            )
            return
        elif int(result["time_out"]) < get_current_time():
            ad_code = str_to_b64(f"{uid}:{str(get_current_time() + 43200)}")
            ad_url = shorten_url(f"https://telegram.me/{U_NAME}?start={ad_code}")
            app.send_message(
                message.chat.id,
                f"Hey **{message.from_user.mention}** \n\nYour Ads token is expired, refresh your token and try again. \n\n**Token Timeout:** 12 hour \n\n**What is token?** \nThis is an ads token. If you pass 1 ad, you can use the bot for 12 hour after passing the ad.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Click Here To Refresh Token",
                                url=f"https://telegram.me/{U_NAME}?start={ad_code}",
                            )
                        ]
                    ]
                ),
                reply_to_message_id=message.id,
            )
            return
        
    if bypasser.ispresent(ddllist, urls[0]):
        msg = app.send_message(
            message.chat.id, "⚡ __generating...__", reply_to_message_id=message.id
        )
    elif bypasser.ispresent(scrapper_sites, urls[0]):
        msg = app.send_message(
            message.chat.id, "⚡ __scrapping...__", reply_to_message_id=message.id
        )
    else:
        msg = app.send_message(
            message.chat.id, "🔎 __bypassing...__", reply_to_message_id=message.id
        )

    link = ""
    for ele in urls:
        if re.search(r"https?:\/\/(?:[\w.-]+)?\.\w+\/\d+:", ele):
            handleIndex(ele, message, msg)
            return
        elif bypasser.ispresent(ddllist, ele):
            try:
                temp = ddl.direct_link_generator(ele)
            except Exception as e:
                temp = "**Error**: " + str(e)
        elif bypasser.ispresent(scrapper_sites, ele):
            try:
                temp = scrapper(ele)
            except Exception as e:
                temp = "**Error**: " + str(e)
        else:
            try:
                temp = bypasser.shortners(ele)
            except Exception as e:
                temp = "**Error**: " + str(e)
        print("bypassed:", temp)
        if temp is not None:
            link = link + temp + "\n\n"


    if otherss:
        try:
            app.send_photo(message.chat.id, message.photo.file_id, f'__{link}__', reply_to_message_id=message.id)
            app.delete_messages(message.chat.id,[msg.id])
            return
        except: pass

    try:
        app.edit_message_text(
            message.chat.id, msg.id, f"__{link}__", disable_web_page_preview=True
        )
    except BaseException:
        try:
            app.edit_message_text(message.chat.id, msg.id, "__Failed to Bypass__")
        except BaseException:
            try:
                app.delete_messages(message.chat.id, msg.id)
            except BaseException:
                pass
            app.send_message(message.chat.id, "__Failed to Bypass__")


# start command
@app.on_message(filters.command(["start"]))
async def send_start(
    client: pyrogram.client.Client,
    message: pyrogram.types.messages_and_media.message.Message,
):
    if str(message.chat.id).startswith("-100") and message.chat.id not in GROUP_ID:
        return
    if UPDATES_CHANNEL is not None:
        try:
            user = await client.get_chat_member(UPDATES_CHANNEL, message.from_user.id)
            if user.status == enums.ChatMemberStatus.BANNED:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"__Sorry, you are banned. Contact My [ Owner ](https://telegram.me/{OWNER_USERNAME})__",
                    disable_web_page_preview=True,
                )
                return
        except UserNotParticipant:
            await client.send_photo(
                chat_id=message.chat.id,
                photo="https://te.legra.ph/file/95db9bf6f91bd96d7a9f1.jpg",
                caption="<i>Join Channel To Use Me🔐</i>",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Join Now 🔓", url=f"https://t.me/{UPDATES_CHANNEL}"
                            )
                        ]
                    ]
                ),
            )
            return
        except Exception as e:
            await client.send_message(
                chat_id=message.chat.id,
                text=f"<i>Something went wrong</i> <b> <a href='https://telegram.me/{OWNER_USERNAME}'>CLICK HERE FOR SUPPORT </a></b> \n\n {e}",
                disable_web_page_preview=True,
            )
            return
    if message.text.startswith("/start ") and len(message.text) > 7:
        user_id = message.from_user.id
        try:
            ad_msg = b64_to_str(message.text.split("/start ")[1])
            if int(user_id) != int(ad_msg.split(":")[0]):
                await app.send_message(
                    message.chat.id,
                    "This Token Is Not For You",
                    reply_to_message_id=message.id,
                )
                return
            if int(ad_msg.split(":")[1]) < get_current_time():
                await app.send_message(
                    message.chat.id,
                    "Token Expired Regenerate A New Token",
                    reply_to_message_id=message.id,
                )
                return
            if int(ad_msg.split(":")[1]) > int(get_current_time() + 43200):
                await app.send_message(
                    message.chat.id,
                    "Dont Try To Be Over Smart",
                    reply_to_message_id=message.id,
                )
                return
            query = {"user_id": user_id}
            collection.update_one(
                query, {"$set": {"time_out": int(ad_msg.split(":")[1])}}, upsert=True
            )
            await app.send_message(
                message.chat.id,
                "Congratulations! Ads token refreshed successfully! \n\nIt will expire after 12 Hour",
                reply_to_message_id=message.id,
            )
            return
        except BaseException:
            await app.send_message(
                message.chat.id,
                "Invalid Token",
                reply_to_message_id=message.id,
            )
            return
    await app.send_message(message.chat.id, f"__👋 Hi **{message.from_user.mention}**, i am Link Bypasser Bot, just send me any supported links and i will you get you results.\nCheckout /help to Read More__",
                           reply_markup=InlineKeyboardMarkup([[ InlineKeyboardButton("❤️ Owner ❤️", url=f"https://telegram.me/{OWNER_USERNAME}")]]), reply_to_message_id=message.id)


# help command
@app.on_message(filters.command(["help"]))
async def send_help(
    client: pyrogram.client.Client,
    message: pyrogram.types.messages_and_media.message.Message,
):
    if str(message.chat.id).startswith("-100") and message.chat.id not in GROUP_ID:
        return
    if UPDATES_CHANNEL is not None:
        try:
            user = await client.get_chat_member(UPDATES_CHANNEL, message.from_user.id)
            if user.status == enums.ChatMemberStatus.BANNED:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"__Sorry, you are banned. Contact My [ Owner ](https://telegram.me/{OWNER_USERNAME})__",
                    disable_web_page_preview=True,
                )
                return
        except UserNotParticipant:
            await client.send_photo(
                chat_id=message.chat.id,
                photo="https://te.legra.ph/file/95db9bf6f91bd96d7a9f1.jpg",
                caption="<i>Join Channel To Use Me🔐</i>",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Join Now 🔓", url=f"https://t.me/{UPDATES_CHANNEL}"
                            )
                        ]
                    ]
                ),
            )
            return
        except Exception as e:
            await client.send_message(
                chat_id=message.chat.id,
                text=f"<i>Something went wrong</i> <b> <a href='https://telegram.me/{OWNER_USERNAME}'>CLICK HERE FOR SUPPORT </a></b> \n\n {e}",
                disable_web_page_preview=True,
            )
            return

    await app.send_message(
        message.chat.id,
        HELP_TEXT,
        reply_to_message_id=message.id,
        disable_web_page_preview=True,
    )

@app.on_message(filters.command(["authorize"]))
async def send_help(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    result = collection.find_one({"role":"admin"})
    ADMIN_LIST = result["value"]
    result = collection.find_one({"role":"auth_chat"})
    GROUP_ID = result["value"]
    if message.chat.id in ADMIN_LIST or message.from_user.id in ADMIN_LIST :
        try :
            msg = int(message.text.split()[-1])
        except ValueError:
            await app.send_message(message.chat.id, f"Example\n<code>/authorize -100</code>", reply_to_message_id=message.id, disable_web_page_preview=True)
            return
        if msg in GROUP_ID:
            await app.send_message(message.chat.id, f"Already Added", reply_to_message_id=message.id, disable_web_page_preview=True)
        else :
            GROUP_ID.append(msg)
            collection.update_one({"role":"auth_chat"}, {"$set": {"value":GROUP_ID}}, upsert=True)
            await app.send_message(message.chat.id, f"Authorized Temporarily!", reply_to_message_id=message.id, disable_web_page_preview=True)
    else:
        await app.send_message(message.chat.id, f"This Command Is Only For Admins", reply_to_message_id=message.id, disable_web_page_preview=True)

@app.on_message(filters.command(["unauthorize"]))
async def send_help(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    result = collection.find_one({"role":"admin"})
    ADMIN_LIST = result["value"]
    result = collection.find_one({"role":"auth_chat"})
    GROUP_ID = result["value"]
    if message.chat.id in ADMIN_LIST or message.from_user.id in ADMIN_LIST :
        try :
            msg = int(message.text.split()[-1])
        except ValueError:
            await app.send_message(message.chat.id, f"Example\n<code>/unauthorize -100</code>", reply_to_message_id=message.id, disable_web_page_preview=True)
            return
        if msg not in GROUP_ID:
            await app.send_message(message.chat.id, f"Already Removed", reply_to_message_id=message.id, disable_web_page_preview=True)
        else :
            if msg == int(PERMANENT_GROUP) :
                await app.send_message(message.chat.id, f"Even Owner Can't Remove This {msg} Chat 😂😂", reply_to_message_id=message.id, disable_web_page_preview=True)
                return
            GROUP_ID.remove(msg)
            collection.update_one({"role":"auth_chat"}, {"$set": {"value":GROUP_ID}}, upsert=True)
            await app.send_message(message.chat.id, f"Unauthorized!", reply_to_message_id=message.id, disable_web_page_preview=True)
    else:
        await app.send_message(message.chat.id, f"This Command Is Only For Admins", reply_to_message_id=message.id, disable_web_page_preview=True)

@app.on_message(filters.command(["addsudo"]))
async def send_help(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    result = collection.find_one({"role":"admin"})
    ADMIN_LIST = result["value"]
    if message.chat.id == int(OWNER_ID) or message.from_user.id == int(OWNER_ID) :
        try :
            msg = int(message.text.split()[-1])
        except ValueError:
            await app.send_message(message.chat.id, f"Example\n<code>/addsudo 123</code>", reply_to_message_id=message.id, disable_web_page_preview=True)
            return
        if msg in ADMIN_LIST:
            await app.send_message(message.chat.id, f"Already Admin", reply_to_message_id=message.id, disable_web_page_preview=True)
        else :
            ADMIN_LIST.append(msg)
            collection.update_one({"role":"admin"}, {"$set": {"value":ADMIN_LIST}}, upsert=True)
            await app.send_message(message.chat.id, f"Promoted As Admin Temporarily", reply_to_message_id=message.id, disable_web_page_preview=True)
    else:
        await app.send_message(message.chat.id, f"This Command Is Only For Owner", reply_to_message_id=message.id, disable_web_page_preview=True)
        
@app.on_message(filters.command(["remsudo"]))
async def send_help(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    result = collection.find_one({"role":"admin"})
    ADMIN_LIST = result["value"]
    if message.chat.id == int(OWNER_ID) or message.from_user.id == int(OWNER_ID) :
        try :
            msg = int(message.text.split()[-1])
        except ValueError:
            await app.send_message(message.chat.id, f"Example\n<code>/remsudo 123</code>", reply_to_message_id=message.id, disable_web_page_preview=True)
            return
        if msg not in ADMIN_LIST:
            await app.send_message(message.chat.id, f"Already Demoted!", reply_to_message_id=message.id, disable_web_page_preview=True)
        else :
            if msg == int(message.from_user.id) :
                await app.send_message(message.chat.id, f"You Can't Remove Yourself 😂😂", reply_to_message_id=message.id, disable_web_page_preview=True)
                return
            elif msg == int(OWNER_ID) :
                await app.send_message(message.chat.id, f"Even Owner Can't Remove Himself 😂😂", reply_to_message_id=message.id, disable_web_page_preview=True)
                return
            ADMIN_LIST.remove(msg)
            collection.update_one({"role":"admin"}, {"$set": {"value":ADMIN_LIST}}, upsert=True)
            await app.send_message(message.chat.id, f"Demoted!", reply_to_message_id=message.id, disable_web_page_preview=True)
    else:
        await app.send_message(message.chat.id, f"This Command Is Only For Owner", reply_to_message_id=message.id, disable_web_page_preview=True)
        
@app.on_message(filters.command(["users"]))
async def send_help(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    result = collection.find_one({"role":"admin"})
    ADMIN_LIST = result["value"]
    result = collection.find_one({"role":"auth_chat"})
    GROUP_ID = result["value"]
    if message.chat.id in ADMIN_LIST or message.from_user.id in ADMIN_LIST :
        lol = "List Of Authorized Chats\n\n"
        for i in GROUP_ID:
            lol += "<code>" + str(i) + "</code>\n"
        lol += "\nList Of Admin ID's\n\n"
        for i in ADMIN_LIST:
            lol += "<code>" + str(i) + "</code>\n"
        await app.send_message(message.chat.id, lol, reply_to_message_id=message.id, disable_web_page_preview=True)
    else :
        await app.send_message(message.chat.id, f"This Command Is Only For Admins", reply_to_message_id=message.id, disable_web_page_preview=True)

# links
@app.on_message(filters.text)
async def receive(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    if str(message.chat.id).startswith("-100") and message.chat.id not in GROUP_ID:
        return
    if UPDATES_CHANNEL is not None:
        try:
            user = await client.get_chat_member(UPDATES_CHANNEL, message.from_user.id)
            if user.status == enums.ChatMemberStatus.BANNED:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"__Sorry, you are banned. Contact My [ Owner ](https://telegram.me/{OWNER_USERNAME})__",
                    disable_web_page_preview=True,
                )
                return
        except UserNotParticipant:
            await client.send_photo(
                chat_id=message.chat.id,
                photo="https://te.legra.ph/file/95db9bf6f91bd96d7a9f1.jpg",
                caption="<i>Join Channel To Use Me🔐</i>",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Join Now 🔓", url=f"https://t.me/{UPDATES_CHANNEL}"
                            )
                        ]
                    ]
                ),
            )
            return
        except Exception as e:
            await client.send_message(
                chat_id=message.chat.id,
                text=f"<i>Something went wrong</i> <b> <a href='https://telegram.me/{OWNER_USERNAME}'>CLICK HERE FOR SUPPORT </a></b> \n\n {e}",
                disable_web_page_preview=True,
            )
            return

    bypass = threading.Thread(target=lambda:loopthread(message),daemon=True)
    bypass.start()


# doc thread
def docthread(message):
    msg = app.send_message(message.chat.id, "🔎 **Bypassing...**", reply_to_message_id=message.id)
    print("sent DLC file")
    sess = requests.session()
    file = app.download_media(message)
    dlccont = open(file,"r").read()
    link = bypasser.getlinks(dlccont,sess)
    app.edit_message_text(message.chat.id, msg.id, f'**{link}**')
    os.remove(file)

# files
@app.on_message(filters.document | filters.photo | filters.video)
def docfile(
    client: pyrogram.client.Client,
    message: pyrogram.types.messages_and_media.message.Message,
):
    if str(message.chat.id).startswith("-100") and message.chat.id not in GROUP_ID:
        return
    if UPDATES_CHANNEL is not None:
        try:
            user = client.get_chat_member(UPDATES_CHANNEL, message.from_user.id)
            if user.status == enums.ChatMemberStatus.BANNED:
                client.send_message(
                    chat_id=message.chat.id,
                    text=f"__Sorry, you are banned. Contact My [ Owner ](https://telegram.me/{OWNER_USERNAME})__",
                    disable_web_page_preview=True,
                )
                return
        except UserNotParticipant:
            client.send_photo(
                chat_id=message.chat.id,
                photo="https://te.legra.ph/file/95db9bf6f91bd96d7a9f1.jpg",
                caption="<i>Join Channel To Use Me🔐</i>",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Join Now 🔓", url=f"https://t.me/{UPDATES_CHANNEL}"
                            )
                        ]
                    ]
                ),
            )
            return
        except Exception as e:
            client.send_message(
                chat_id=message.chat.id,
                text=f"<i>Something went wrong</i> <b> <a href='https://telegram.me/{OWNER_USERNAME}'>CLICK HERE FOR SUPPORT </a></b> \n\n {e}",
                disable_web_page_preview=True,
            )
            return

    try:
        if message.document.file_name.endswith("dlc"):
            bypass = threading.Thread(target=lambda: docthread(message), daemon=True)
            bypass.start()
            return
    except BaseException:
        pass

    bypass = threading.Thread(target=lambda: loopthread(message, True), daemon=True)
    bypass.start()

# server loop
print("Bot Starting")
app.run()




