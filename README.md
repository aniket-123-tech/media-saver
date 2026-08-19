[import telebot.py](https://github.com/user-attachments/files/30712058/import.telebot.py)
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import string
import random
import time

# ================= KHOOD KI DETAILS =================
API_ID = 35237965  
API_HASH = "ca376f2bed12f0efced887b7ae90e067"  
BOT_TOKEN = "8745032512:AAE1aUo7_PlZJzy4rlGtj038M-EibtIlwcs"  
OWNER_ID = 5884320645  
ADMIN_USERNAME = "KILLER_367"  # Bina '@' ke
# ====================================================

# ================= PREMIUM PLANS SETUP =================
MAX_FREE_LINKS = 3  

PLAN_1_DAYS = "1 Days"
PLAN_1_PRICE = "₹10"

PLAN_2_DAYS = "7 Days"
PLAN_2_PRICE = "₹40"

PLAN_3_DAYS = "30 Days"
PLAN_3_PRICE = "₹100"
# =======================================================

app = Client("MediaSaverBotPro", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

MEDIA_DATABASE = {}
pending_groups = {}  
USER_USAGE = {}  
PREMIUM_USERS = {}  
ALL_USERS = set() # NAYA: Saare users ko track karne ke liye

PREMIUM_DATA = {
    "qr_file_id": None 
}
ADMIN_STATE = {}

def generate_unique_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# ================= ADMIN DASHBOARD COMMANDS =================

# 1. TOTAL USERS CHECK KARNA
@app.on_message(filters.private & filters.command("users") & filters.user(OWNER_ID))
async def show_all_users(client, message):
    total = len(ALL_USERS)
    await message.reply_text(f"📊 **Bot Statistics**\n\nTotal Users: **{total}**\n_(Jinhone bot ko start kiya hai)_")

# 2. PREMIUM LIST CHECK KARNA
@app.on_message(filters.private & filters.command("premiumlist") & filters.user(OWNER_ID))
async def show_premium_list(client, message):
    if not PREMIUM_USERS:
        await message.reply_text("📂 Abhi tak koi Premium User nahi hai.")
        return
    
    text = "💎 **Premium Users List:**\n\n"
    current_time = time.time()
    
    for i, (user_id, expiry) in enumerate(PREMIUM_USERS.items(), 1):
        remaining_days = max(0, int((expiry - current_time) / 86400))
        text += f"{i}. User ID: `{user_id}` ⏳ Expire In: **{remaining_days} Days**\n"
        
    await message.reply_text(text)

# 3. BROADCAST / GCAST MESSAGE
@app.on_message(filters.private & filters.command("gcast") & filters.user(OWNER_ID))
async def broadcast_message(client, message):
    is_reply = True if message.reply_to_message else False
    
    if not is_reply and len(message.command) < 2:
        await message.reply_text("⚠️ **Format:** `/gcast Hello everyone!`\nYa phir kisi photo/message par reply karke `/gcast` likhein.")
        return

    wait_msg = await message.reply_text("⏳ Broadcast shuru ho raha hai... Please wait.")
    
    success_count = 0
    failed_count = 0

    for user_id in ALL_USERS:
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
            
    await wait_msg.edit_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"🟢 Sent Successfully: **{success_count}**\n"
        f"🔴 Failed/Blocked: **{failed_count}**"
    )

# ================= ADMIN: APPROVE USER =================

@app.on_message(filters.private & filters.command("approve") & filters.user(OWNER_ID))
async def approve_premium(client, message):
    try:
        cmd = message.text.split()
        if len(cmd) < 3:
            await message.reply_text("⚠️ **Format:** `/approve User_ID Days`\nJaise: `/approve 123456789 30`")
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
        PREMIUM_USERS[target_user_id] = expiry_time
        ALL_USERS.add(target_user_id) 
        
        await message.reply_text(f"✅ **Premium Approved!**\n👤 User: {user.first_name} (`{target_user_id}`)\n⏳ Duration: **{days} Days**")
        
        await client.send_message(
            target_user_id,
            f"🎉 **Congratulations!**\nAdmin ne aapko **{days} Days** ke liye Premium access de diya hai!"
        )
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# ================= ADMIN: PREMIUM QR SETUP =================

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
        MEDIA_DATABASE[unique_code] = media_list 
        bot_info = await client.get_me()
        link = f"https://t.me/{bot_info.username}?start={unique_code}"
        await message.reply_text(f"✅ **Album Saved! ({len(media_list)} Files)**\n🔗 **Link:**\n`{link}`", quote=True)

@app.on_message(filters.private & filters.user(OWNER_ID) & (filters.document | filters.video | filters.photo | filters.audio))
async def save_media(client, message):
    if ADMIN_STATE.get(OWNER_ID) == "WAITING_FOR_QR" and message.photo:
        PREMIUM_DATA["qr_file_id"] = message.photo.file_id
        ADMIN_STATE[OWNER_ID] = None  
        await message.reply_text(f"🎉 **QR Code Saved!**\nPremium Setup Complete.")
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
        MEDIA_DATABASE[unique_code] = [media_data] 
        bot_info = await client.get_me()
        link = f"https://t.me/{bot_info.username}?start={unique_code}"
        await message.reply_text(f"✅ **Single Media Saved!**\n🔗 **Link:**\n`{link}`", quote=True)

# ================= USER ACCESS & FREEMIUM LOGIC =================

@app.on_message(filters.private & filters.command("start"))
async def handle_start(client, message):
    ALL_USERS.add(message.from_user.id)
    
    text = message.text.split()
    user_id = message.from_user.id
    
    if len(text) == 1:
        await message.reply_text("Hello! Main ek Premium Media Bot hu. Mujhe links ke through access karein.")
        return
    
    unique_code = text[1]
    
    if unique_code in MEDIA_DATABASE:
        is_premium = False
        if user_id in PREMIUM_USERS:
            if time.time() < PREMIUM_USERS[user_id]:
                is_premium = True
            else:
                del PREMIUM_USERS[user_id]
                await client.send_message(user_id, "⚠️ **Plan Expired:** Aapka premium khatam ho gaya hai.")

        if user_id != OWNER_ID and not is_premium:
            current_usage = USER_USAGE.get(user_id, 0)
            if current_usage >= MAX_FREE_LINKS:
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💎 Buy Premium Now", callback_data="buy_premium")]])
                await message.reply_text("🚫 **Free Limit Reached!**\nPremium kharidein unlimited access ke liye.", reply_markup=keyboard)
                return  
            else:
                USER_USAGE[user_id] = current_usage + 1
        
        media_list = MEDIA_DATABASE[unique_code]
        status_msg = ""
        if user_id != OWNER_ID:
            if is_premium: status_msg = "\n💎 _Premium Member_"
            else: status_msg = f"\n💡 _Free Links Left: {MAX_FREE_LINKS - USER_USAGE[user_id]}_"

        await message.reply_text(f"📂 Aapko **{len(media_list)} files** mil rahi hain. (5 Min Auto-Delete){status_msg}")
        
        sent_message_ids = []
        try:
            for index, media in enumerate(media_list):
                file_id, media_type = media["file_id"], media["type"]
                caption = "⏳ **5 min auto-delete**" if index == len(media_list) - 1 else ""
                
                sent_msg = None
                if media_type == "document": sent_msg = await client.send_document(message.chat.id, file_id, caption=caption)
                elif media_type == "video": sent_msg = await client.send_video(message.chat.id, file_id, caption=caption)
                elif media_type == "photo": sent_msg = await client.send_photo(message.chat.id, file_id, caption=caption)
                elif media_type == "audio": sent_msg = await client.send_audio(message.chat.id, file_id, caption=caption)
                
                if sent_msg: sent_message_ids.append(sent_msg.id)
                await asyncio.sleep(0.5) 
            
            if sent_message_ids:
                await asyncio.sleep(300) 
                await client.delete_messages(chat_id=message.from_user.id, message_ids=sent_message_ids)
        except Exception as e:
            await message.reply_text("❌ Media bhejne me error.")
    else:
        await message.reply_text("❌ Yeh link invalid ya expire ho chuka hai.")

# ================= BUTTON CALLBACK LOGIC (3 PLANS DISPLAY) =================

@app.on_callback_query(filters.regex("buy_premium"))
async def show_premium_details(client, callback_query):
    if PREMIUM_DATA["qr_file_id"] is None:
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
        photo=PREMIUM_DATA["qr_file_id"],
        caption=plan_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 Send Screenshot", url=f"https://t.me/{ADMIN_USERNAME}")]])
    )

# ================= BACKGROUND TASK (DAILY REMINDER) =================

async def daily_premium_check():
    while True:
        await asyncio.sleep(86400) 
        current_time = time.time()
        
        for user_id, expiry in list(PREMIUM_USERS.items()):
            if current_time >= expiry:
                del PREMIUM_USERS[user_id]
                try: await app.send_message(user_id, "⚠️ **Premium Expired!**\nAapka premium expire ho gaya hai.")
                except: pass
            else:
                remaining_days = int((expiry - current_time) / 86400)
                if remaining_days > 0:
                    try: await app.send_message(user_id, f"🔔 **Premium Reminder:**\nAapka premium **{remaining_days} din** me expire hoga.")
                    except: pass

# ================= STARTUP LOGIC =================

async def main():
    await app.start()
    ALL_USERS.add(OWNER_ID)
    print("Bot is starting (Admin Dashboard Features Active)...")
    asyncio.create_task(daily_premium_check())
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())
