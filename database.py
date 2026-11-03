import sqlite3
import json
import threading
import time
from datetime import datetime

# ═══════════════════════════════════════
# 🗄️ فایل دیتابیس SQLite (برای سرعت بالا و جلوگیری از کرش)
# ═══════════════════════════════════════
DB_FILE = "hypersin.db"
_db_lock = threading.Lock()

def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-128000")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # کاربران
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY, coins INTEGER DEFAULT 0,
        joined INTEGER DEFAULT 0, got_start_gift INTEGER DEFAULT 0,
        invite_count INTEGER DEFAULT 0, invited_by TEXT,
        username TEXT, last_daily TEXT, msg_count INTEGER DEFAULT 0,
        last_wheel TEXT, invite_reward_paid INTEGER DEFAULT 0,
        used_gift_codes TEXT DEFAULT '[]',
        guaranteed_members TEXT DEFAULT '{}',
        last_guaranteed_times TEXT DEFAULT '{}',
        joined_at TEXT, is_vip INTEGER DEFAULT 0, vip_expire TEXT
    )''')
    # سفارش سین
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY, user_id TEXT, count INTEGER,
        message_id INTEGER, reply_message_id INTEGER,
        seen_count INTEGER DEFAULT 0, status TEXT DEFAULT 'active',
        order_number INTEGER
    )''')
    # سفارش عضو
    c.execute('''CREATE TABLE IF NOT EXISTS member_orders (
        id TEXT PRIMARY KEY, user_id TEXT, count INTEGER,
        link TEXT, chat_id TEXT, message_id INTEGER,
        seen_count INTEGER DEFAULT 0, status TEXT DEFAULT 'active',
        order_number INTEGER, order_type TEXT DEFAULT 'normal',
        reward INTEGER DEFAULT 3, chat_type TEXT DEFAULT 'channel'
    )''')
    # رکورد سین
    c.execute('''CREATE TABLE IF NOT EXISTS seen_records (
        order_id TEXT, user_id TEXT, PRIMARY KEY(order_id, user_id)
    )''')
    # رکورد عضو
    c.execute('''CREATE TABLE IF NOT EXISTS member_records (
        order_id TEXT, user_id TEXT, PRIMARY KEY(order_id, user_id)
    )''')
    # کدهای هدیه
    c.execute('''CREATE TABLE IF NOT EXISTS gift_codes (
        code TEXT PRIMARY KEY, coins INTEGER, capacity INTEGER,
        used_by TEXT DEFAULT '[]', vip_code TEXT
    )''')
    # مسدودها
    c.execute('''CREATE TABLE IF NOT EXISTS banned (user_id TEXT PRIMARY KEY)''')
    # ادمین‌ها
    c.execute('''CREATE TABLE IF NOT EXISTS admins (user_id TEXT PRIMARY KEY)''')
    # VIP
    c.execute('''CREATE TABLE IF NOT EXISTS vip (user_id TEXT PRIMARY KEY, expire TEXT)''')
    # کانال‌های جوین اجباری
    c.execute('''CREATE TABLE IF NOT EXISTS join_channels (chat_id TEXT PRIMARY KEY, link TEXT, title TEXT)''')
    # تیکت‌های پشتیبانی
    c.execute('''CREATE TABLE IF NOT EXISTS support_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, name TEXT,
        text TEXT, status TEXT DEFAULT 'open', date TEXT
    )''')
    # چالش‌ها
    c.execute('''CREATE TABLE IF NOT EXISTS challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id TEXT, user_id TEXT,
        target INTEGER, reward INTEGER, status TEXT DEFAULT 'pending',
        invites INTEGER DEFAULT 0, created_at TEXT
    )''')
    # تنظیمات
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    # پاکت‌های سکه
    c.execute('''CREATE TABLE IF NOT EXISTS coin_packets (
        id TEXT PRIMARY KEY, coins INTEGER, capacity INTEGER,
        text TEXT, used_by TEXT DEFAULT '[]'
    )''')
    # آمار
    c.execute('''CREATE TABLE IF NOT EXISTS stats (
        key TEXT PRIMARY KEY, value INTEGER DEFAULT 0
    )''')
    # اخطارها
    c.execute('''CREATE TABLE IF NOT EXISTS admin_warnings (user_id TEXT PRIMARY KEY, count INTEGER DEFAULT 0)''')
    # گروه‌ها (برای تبلیغات)
    c.execute('''CREATE TABLE IF NOT EXISTS group_targets (chat_id TEXT PRIMARY KEY, title TEXT, type TEXT)''')

    # تنظیمات پیش‌فرض
    defaults = {
        "seen_reward": "1", "sin_cost": "1", "member_cost": "5",
        "member_normal_reward": "3", "member_guaranteed_reward": "7",
        "guaranteed_cost": "10", "transfer_fee": "2", "start_gift": "25",
        "daily_gift": "10", "invite_reward": "15", "wheel_cooldown": "43200",
        "guaranteed_hours": "48", "guaranteed_penalty": "7",
        "guaranteed_refund": "5", "guaranteed_cooldown": "300",
        "min_sin": "15", "min_member": "3"
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()

def db_exec(query, params=(), fetchone=False, fetchall=False):
    with _db_lock:
        conn = get_db()
        try:
            c = conn.cursor()
            c.execute(query, params)
            if fetchone:
                return c.fetchone()
            if fetchall:
                return c.fetchall()
            conn.commit()
            return True
        except Exception as e:
            print(f"⚠️ DB: {e}")
            return None
        finally:
            conn.close()

# تابع اتصال اولیه (وقتی کد اصلی این فایل رو ایمپورت میکنه، خودش دیتابیس رو میسازه)
init_db()
