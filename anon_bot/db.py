import sqlite3
from datetime import datetime

DB_NAME = 'users.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE,
                username TEXT,
                subscription_type TEXT DEFAULT 'FREE',
                generated_links INTEGER DEFAULT 0,
                join_date TEXT,
                is_admin BOOLEAN DEFAULT FALSE,
                user_consent BOOLEAN DEFAULT FALSE,
                is_blocked BOOLEAN DEFAULT FALSE  -- Новый флаг для блокировки пользователя
            )
        ''')
        conn.commit()

def add_user(user_id, username):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, join_date)
            VALUES (?, ?, ?)
        ''', (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

def update_generated_links(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET generated_links = generated_links + 1
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()

def get_user_profile(user_id=None, username=None):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Проверяем, что хотя бы один параметр передан
        if user_id is None and username is None:
            raise ValueError("Необходимо передать user_id или username.")
        
        # Формируем SQL-запрос в зависимости от переданных параметров
        if user_id is not None:
            cursor.execute('''
                SELECT username, subscription_type, generated_links, is_admin, is_blocked, user_consent
                FROM users
                WHERE user_id = ?
            ''', (user_id,))
        elif username is not None:
            cursor.execute('''
                SELECT username, subscription_type, generated_links, is_admin, is_blocked, user_consent
                FROM users
                WHERE username = ?
            ''', (username,))
        
        result = cursor.fetchone()
        
        # Если пользователь найден, возвращаем профиль в виде словаря
        if result:
            return {
                'username': result[0],
                'subscription_type': result[1],
                'generated_links': result[2],
                'is_admin': bool(result[3]),
                'is_blocked': bool(result[4]),
                'user_consent': bool(result[5]),
            }
        else:
            return None  # Возвращаем None, если пользователь не найден
        
        
def get_all_users():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        return cursor.fetchall()

def set_admin_status(user_id, is_admin):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET is_admin = ?
            WHERE user_id = ?
        ''', (is_admin, user_id))
        conn.commit()

def set_user_consent(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET user_consent = TRUE
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()

def has_user_accepted_policy(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_consent
            FROM users
            WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else False

# Новые функции

def set_user_subscription(user_id, subscription_type):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET subscription_type = ?
            WHERE user_id = ?
        ''', (subscription_type, user_id))
        conn.commit()

def delete_user(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM users
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()

def block_user(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET is_blocked = TRUE
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()


def get_user_profile_by_username(username):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT username, subscription_type, generated_links, is_admin, is_blocked, user_consent
            FROM users
            WHERE username = ?
        ''', (username,))
        return cursor.fetchone()

def get_user_subscription(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT subscription_type
            FROM users
            WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def get_statistics():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(generated_links) FROM users')
        link_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM users WHERE subscription_type = "PREMIUM"')
        active_subscriptions = cursor.fetchone()[0]

        return {
            'user_count': user_count,
            'link_count': link_count,
            'active_subscriptions': active_subscriptions
        }