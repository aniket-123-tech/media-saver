from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import string
import random
import time
import os
import threading
from flask import Flask
from motor.motor_asyncio import AsyncIOMotorClient

# ================= KHOOD KI DETAILS =================
API_ID = 35237965  
API_HASH = "ca376f2bed12f0efced887b7ae90e067"  
BOT_TOKEN = "8463117288:AAHEbDa2tLhif69cUJa62eXYkTM3edTfyto"  
OWNER_ID = 5884320645  
ADMIN_USERNAME = "KILLER_367"  

# 🛑 AAPKA MONGODB ATLAS LINK 🛑
MONGO_URL = "mongodb+srv://atul_bot:uYEixMY8WZ2MIHqx@cluster0.h2it7bu.mongodb.net/?appName=Cluster0"
# ====================================================

# ================= MONGODB SETUP =================
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client["MediaBotDB"]

users_col = db["users"]           # Total users aur unki free limit
premium_col = db["premium"]       # Premium users ka data
media_col = db["media"]           # Generated links aur unka media
settings_col = db["settings"]     # QR Code aur Custom Link settings
# =================================================

# ================= DUMMY WEB SERVER =================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running perfectly on Render with MongoDB!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# ================= PREMIUM & LIMIT SETTINGS =================
MAX_FREE_LINKS = 3  
LIMIT_RESET_TIME = 86400  # SET TO 24 HOURS (86400 seconds)

PLAN_1_DAYS = "1 Days"
PLAN_1_PRICE = "₹10"

PLAN_2_DAYS = "7 Days"
PLAN_2_PRICE = "₹40"

PLAN_3_DAYS = "30 Days"
PLAN_3_PRICE = "₹100"
# ============================================================

# ✅ IN_MEMORY=TRUE ADD KIYA GAYA HAI TAAKI RENDER PAR CRASH NA HO ✅
app = Client("MediaSaverBotPro", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
pending_groups = {}  
ADMIN_STATE = {}

def generate_unique_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# Helper: Default Settings Ensure Karna
async def get_settings():
    setting = await settings_col.find_one({"_id": "bot_config"})
    if not setting:
        setting = {"_id": "bot_config", "qr_file_id": None, "custom_link": None}
        await settings_col.insert_one(setting)
    return setting

# ================= ADMIN DASHBOARD COMMANDS =================

@app.on_message(filters.private & filters.command("users") & filters.user(OWNER_ID))
async def show_all_users(client, message):
    total = await users_col.count_documents({})
    await message.reply_text(f"📊 **Bot Statistics**\n\nTotal Users: **{total}**\n_(Database me saved hain)_")

@app.on_message(filters.private & filters.command("premiumlist") & filters.user(OWNER_ID))
async def show_premium_list(client, message):
    count = await premium_col.count_documents({})
    if count == 0:
        await message.reply_text("📂 Abhi tak koi Premium User nahi hai.")
        return
    
    text = "💎 **Premium Users List:**\n\n"
    current_time = time.time()
    
    cursor = premium_col.find({})
    i = 1
    async for user in cursor:
        expiry = user["expiry"]
        remaining_days = max(0, int((expiry - current_time) / 86400))
        text += f"{i}. User ID: `{user['_id']}` ⏳ Expire In: **{remaining_days} Days**\n"
        i += 1
        
    await message.reply_text(text)

@app.on_message(filters.private & filters.command("gcast") & filters.user(OWNER_ID))
async def broadcast_message(client, message):
    is_reply = True if message.reply_to_message else False
    if not is_reply and len(message.command) < 2:
        await message.reply_text("⚠️ **Format:** `/gcast Hello everyone!`")
        return

    wait_msg = await message.reply_text("⏳ Broadcast shuru ho raha hai... Please wait.")
    success_count = 0
    failed_count = 0

    cursor = users_col.find({})
    async for user in cursor:
        user_id = user["_id"]
        try:
            if is_reply:
                await message.reply_to_message.copy(user_id)
            else:
                text_to_send = message.text.split(None, 1)[1]
                await client.send_message(user_id, text_to_send)
            success_count += 1
            await asyncio.sleep(0.1)  
        except Exception:
            failed_count += 1
            
    await wait_msg.edit_text(f"✅ **Broadcast Complete!**\n\n🟢 Sent: **{success_count}**\n🔴 Failed/Blocked: **{failed_count}**")

@app.on_message(filters.private & filters.command("setlink") & filters.user(OWNER_ID))
async def set_media_link(client, message):
    cmd = message.text.split(None, 1)
    if len(cmd) < 2:
        await message.reply_text("⚠️ **Format:** `/setlink https://example.com`\n_(Band karne ke liye: `/setlink off`)_")
        return
    
    link = cmd[1].strip()
    if link.lower() == "off":
        await settings_col.update_one({"_id": "bot_config"}, {"$set": {"custom_link": None}}, upsert=True)
        await message.reply_text("✅ **Link Button hataya gaya.** Ab media ke niche button nahi aayega.")
    else:
        await settings_col.update_one({"_id": "bot_config"}, {"$set": {"custom_link": link}}, upsert=True)
        await message.reply_text(f"✅ **Link Set Ho Gaya!**\nAb har media ke niche button is link par jayega:\n{link}")

@app.on_message(filters.private & filters.command("approve") & filters.user(OWNER_ID))
async def approve_premium(client, message):
    try:
        cmd = message.text.split()
        if len(cmd) < 3:
            await message.reply_text("⚠️ **Format:** `/approve User_ID Days`")
            return
        
        target_user = int(cmd[1]) if cmd[1].isdigit() else cmd[1]
        days = int(cmd[2])
            
        try:
            user = await client.get_users(target_user)
            target_user_id = user.id
        except Exception:
            await message.reply_text("❌ User nahi mila.")
            return

        expiry_time = time.time() + (days * 86400) 
        await premium_col.update_one({"_id": target_user_id}, {"$set": {"expiry": expiry_time}}, upsert=True)
        await users_col.update_one({"_id": target_user_id}, {"$setOnInsert": {"count": 0, "last_reset": time.time()}}, upsert=True)
        
        await message.reply_text(f"✅ **Premium Approved!**\n👤 User: {user.first_name} (`{target_user_id}`)\n⏳ Duration: **{days} Days**")
        await client.send_message(target_user_id, f"🎉 **Congratulations!**\nAdmin ne aapko **{days} Days** ke liye Premium access de diya hai!")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@app.on_message(filters.private & filters.command("premium") & filters.user(OWNER_ID))
async def premium_setup(client, message):
    ADMIN_STATE[OWNER_ID] = "WAITING_FOR_QR"
    await message.reply_text("🛠 **Premium Setup!**\nKripya apna **Payment QR Code (Photo)** upload karein.")

# ================= MEDIA UPLOAD =================

async def process_media_group(client, message, group_id):
    await asyncio.sleep(3) 
    if group_id in pending_groups:
        media_list = pending_groups.pop(group_id)
        unique_code = generate_unique_code()
        
        await media_col.insert_one({"_id": unique_code, "files": media_list})
        
        bot_info = await client.get_me()
        link = f"https://t.me/{bot_info.username}?start={unique_code}"
        await message.reply_text(f"✅ **Album Saved Database Me! ({len(media_list)} Files)**\n🔗 **Link:**\n`{link}`", quote=True)

@app.on_message(filters.private & filters.user(OWNER_ID) & (filters.document | filters.video | filters.photo | filters.audio))
async def save_media(client, message):
    if ADMIN_STATE.get(OWNER_ID) == "WAITING_FOR_QR" and message.photo:
        await settings_col.update_one({"_id": "bot_config"}, {"$set": {"qr_file_id": message.photo.file_id}}, upsert=True)
        ADMIN_STATE[OWNER_ID] = None  
        await message.reply_text(f"🎉 **QR Code Saved in DB!**\nPremium Setup Complete.")
        return 

    if message.document: file_id, media_type = message.document.file_id, "document"
    elif message.video: file_id, media_type = message.video.file_id, "video"
    elif message.photo: file_id, media_type = message.photo.file_id, "photo"
    elif message.audio: file_id, media_type = message.audio.file_id, "audio"
    else: return

    media_data = {"file_id": file_id, "type": media_type}

    if message.media_group_id:
        group_id = message.media_group_id
        if group_id not in pending_groups:
            pending_groups[group_id] = [media_data]
            asyncio.create_task(process_media_group(client, message, group_id))
        else:
            pending_groups[group_id].append(media_data)
    else:
        unique_code = generate_unique_code()
        await media_col.insert_one({"_id": unique_code, "files": [media_data]})
        bot_info = await client.get_me()
        link = f"https://t.me/{bot_info.username}?start={unique_code}"
        await message.reply_text(f"✅ **Single Media Saved in DB!**\n🔗 **Link:**\n`{link}`", quote=True)

# ================= USER ACCESS & FREEMIUM LOGIC =================

@app.on_message(filters.private & filters.command("start"))
async def handle_start(client, message):
    user_id = message.from_user.id
    current_time = time.time()
    
    # DB me user add karein (agar naya hai)
    await users_col.update_one({"_id": user_id}, {"$setOnInsert": {"count": 0, "last_reset": current_time}}, upsert=True)
    
    text = message.text.split()
    if len(text) == 1:
        await message.reply_text("Hello! Main ek Premium Media Bot hu. Mujhe links ke through access karein.")
        return
    
    unique_code = text[1]
    media_data = await media_col.find_one({"_id": unique_code})
    
    if media_data:
        is_premium = False
        prem_user = await premium_col.find_one({"_id": user_id})

        if prem_user:
            if current_time < prem_user["expiry"]:
                is_premium = True
            else:
                await premium_col.delete_one({"_id": user_id})
                await client.send_message(user_id, "⚠️ **Plan Expired:** Aapka premium khatam ho gaya hai.")

        user_db = await users_col.find_one({"_id": user_id})
        
        if user_id != OWNER_ID and not is_premium:
            if current_time - user_db.get("last_reset", 0) >= LIMIT_RESET_TIME:
                await users_col.update_one({"_id": user_id}, {"$set": {"count": 0, "last_reset": current_time}})
                user_db["count"] = 0
            
            if user_db["count"] >= MAX_FREE_LINKS:
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💎 Buy Premium Now", callback_data="buy_premium")]])
                await message.reply_text(
                    "🚫 **Free Limit Reached!**\n\nAapki free limit khatam ho chuki hai.\nAbhi aur dekhne ke liye Premium kharidein.", 
                    reply_markup=keyboard
                )
                return  
            else:
                await users_col.update_one({"_id": user_id}, {"$inc": {"count": 1}})
                user_db["count"] += 1
        
        media_list = media_data["files"]
        status_msg = ""
        if user_id != OWNER_ID:
            if is_premium: status_msg = "\n💎 _Premium Member_"
            else: status_msg = f"\n💡 _Free Links Left: {MAX_FREE_LINKS - user_db['count']}_"

        await message.reply_text(f"📂 Aapko **{len(media_list)} files** mil rahi hain. (5 Min Auto-Delete){status_msg}")
        
        settings = await get_settings()
        reply_markup = None
        if settings.get("custom_link"):
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🎬 Videos", url=settings["custom_link"])]])
        
        sent_message_ids = []
        try:
            for index, media in enumerate(media_list):
                file_id, media_type = media["file_id"], media["type"]
                caption = "⏳ **5 min auto-delete**" if index == len(media_list) - 1 else ""
                
                sent_msg = None
                if media_type == "document": sent_msg = await client.send_document(message.chat.id, file_id, caption=caption, reply_markup=reply_markup)
                elif media_type == "video": sent_msg = await client.send_video(message.chat.id, file_id, caption=caption, reply_markup=reply_markup)
                elif media_type == "photo": sent_msg = await client.send_photo(message.chat.id, file_id, caption=caption, reply_markup=reply_markup)
                elif media_type == "audio": sent_msg = await client.send_audio(message.chat.id, file_id, caption=caption, reply_markup=reply_markup)
                
                if sent_msg: sent_message_ids.append(sent_msg.id)
                await asyncio.sleep(0.5) 
            
            if sent_message_ids:
                await asyncio.sleep(300) 
                await client.delete_messages(chat_id=message.from_user.id, message_ids=sent_message_ids)
        except Exception as e:
            await message.reply_text(f"❌ Media bhejne me error: {e}")
    else:
        await message.reply_text("❌ Yeh link invalid ya expire ho chuka hai.")

# ================= BUTTON CALLBACK LOGIC =================

@app.on_callback_query(filters.regex("buy_premium"))
async def show_premium_details(client, callback_query):
    settings = await get_settings()
    qr_id = settings.get("qr_file_id")
    
    if not qr_id:
        await callback_query.message.edit_text(f"🛠 **Plan Update Ho Raha Hai!**\nAdmin ko message karein: @{ADMIN_USERNAME}")
        return

    plan_text = (
        f"💎 **PREMIUM SUBSCRIPTION PLANS** 💎\n\n"
        f"🥇 **Plan 1:** {PLAN_1_DAYS} - **{PLAN_1_PRICE}**\n"
        f"🥈 **Plan 2:** {PLAN_2_DAYS} - **{PLAN_2_PRICE}**\n"
        f"🥉 **Plan 3:** {PLAN_3_DAYS} - **{PLAN_3_PRICE}**\n\n"
        f"**👉 Kaise Kharidein?**\n"
        f"1. Upar diye QR Code par apne pasand ke plan ka amount pay karein.\n"
        f"2. Payment ka Screenshot lein.\n"
        f"3. Niche button click karke @{ADMIN_USERNAME} ko bhej dein."
    )
    
    await callback_query.message.delete()
    await client.send_photo(
        chat_id=callback_query.from_user.id,
        photo=qr_id,
        caption=plan_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 Send Screenshot", url=f"https://t.me/{ADMIN_USERNAME}")]])
    )

# ================= BACKGROUND TASKS (DB WALE) =================

async def daily_premium_check():
    while True:
        await asyncio.sleep(86400) 
        current_time = time.time()
        cursor = premium_col.find({})
        async for user in cursor:
            if current_time >= user["expiry"]:
                await premium_col.delete_one({"_id": user["_id"]})
                try: await app.send_message(user["_id"], "⚠️ **Premium Expired!**\nAapka premium expire ho gaya hai.")
                except: pass
            else:
                remaining_days = int((user["expiry"] - current_time) / 86400)
                if remaining_days > 0:
                    try: await app.send_message(user["_id"], f"🔔 **Premium Reminder:**\nAapka premium **{remaining_days} din** me expire hoga.")
                    except: pass

async def free_limit_reset_check():
    while True:
        # Check every 60 seconds instead of 2 seconds in production to save resources
        await asyncio.sleep(60) 
        current_time = time.time()
        
        # Un users ko dhundo jinka count 0 se bada hai
        cursor = users_col.find({"count": {"$gt": 0}})
        async for user in cursor:
            if current_time - user.get("last_reset", 0) >= LIMIT_RESET_TIME:
                await users_col.update_one({"_id": user["_id"]}, {"$set": {"count": 0, "last_reset": current_time}})
                try:
                    await app.send_message(
                        user["_id"], 
                        "🔔 **Good News!**\n\nAapki free limit reset ho gayi hai. 🎉\n"
                        f"Ab aap wapas **{MAX_FREE_LINKS} links** bilkul free me use kar sakte hain!"
                    )
                except Exception:
                    pass

# ================= STARTUP LOGIC =================

async def main():
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    
    await app.start()
    print("Bot is started with MongoDB Database! (Ready for 24/7 Deployment)")
    
    asyncio.create_task(daily_premium_check())
    asyncio.create_task(free_limit_reset_check())
    
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())
