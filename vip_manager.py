# vip_manager.py (فایل جدید)
import json
import os

VIP_FILE = "vip_users.json"

def load_vip_users():
    """بارگذاری لیست کاربران VIP"""
    if os.path.exists(VIP_FILE):
        with open(VIP_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_vip_users(users_dict):
    """ذخیره لیست کاربران VIP"""
    with open(VIP_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_dict, f, ensure_ascii=False, indent=2)

def add_vip_user(user_id, username=""):
    """اضافه کردن کاربر VIP"""
    users = load_vip_users()
    users[str(user_id)] = {
        "active": True,
        "username": username,
        "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_vip_users(users)

def remove_vip_user(user_id):
    """حذف کاربر VIP"""
    users = load_vip_users()
    if str(user_id) in users:
        del users[str(user_id)]
        save_vip_users(users)

def is_vip(user_id):
    """چک کردن وضعیت VIP بودن"""
    users = load_vip_users()
    user_data = users.get(str(user_id))
    return user_data and user_data.get("active", False)
