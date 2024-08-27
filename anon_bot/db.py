import psycopg2
from datetime import datetime
import config

def get_connection():
    """Функция для получения подключения к базе данных."""
    return psycopg2.connect(
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT
    )

def init_db():
    """Инициализация базы данных и создание таблиц."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE,
                    username TEXT,
                    subscription_type TEXT DEFAULT 'FREE',
                    generated_links INTEGER DEFAULT 0,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_admin BOOLEAN DEFAULT FALSE,
                    user_consent BOOLEAN DEFAULT FALSE,
                    is_blocked BOOLEAN DEFAULT FALSE
                )
            ''')
            conn.commit()

def check_and_init_db():
    """Проверка наличия таблицы и ее инициализация, если отсутствует."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.users');")
            if cursor.fetchone()[0] is None:
                init_db()

def add_user(user_id, username):
    """Добавление нового пользователя в базу данных."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO users (user_id, username, join_date)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING;
            ''', (user_id, username, datetime.now()))
            conn.commit()

def update_generated_links(user_id):
    """Обновление количества сгенерированных ссылок для пользователя."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                UPDATE users
                SET generated_links = generated_links + 1
                WHERE user_id = %s;
            ''', (user_id,))
            conn.commit()

def get_user_profile(user_id=None, username=None):
    """Получение профиля пользователя по user_id или username."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            if user_id is None and username is None:
                raise ValueError("Необходимо передать user_id или username.")
            
            if user_id is not None:
                cursor.execute('''
                    SELECT username, subscription_type, generated_links, is_admin, is_blocked, user_consent
                    FROM users
                    WHERE user_id = %s;
                ''', (user_id,))
            elif username is not None:
                cursor.execute('''
                    SELECT username, subscription_type, generated_links, is_admin, is_blocked, user_consent
                    FROM users
                    WHERE username = %s;
                ''', (username,))
            
            result = cursor.fetchone()
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
                return None

def get_all_users():
    """Получение списка всех пользователей."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT user_id FROM users;')
            return cursor.fetchall()

def set_admin_status(user_id, is_admin):
    """Установка статуса администратора для пользователя."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                UPDATE users
                SET is_admin = %s
                WHERE user_id = %s;
            ''', (is_admin, user_id))
            conn.commit()

def set_user_consent(user_id):
    """Установка согласия пользователя."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                UPDATE users
                SET user_consent = TRUE
                WHERE user_id = %s;
            ''', (user_id,))
            conn.commit()

def has_user_accepted_policy(user_id):
    """Проверка, принял ли пользователь политику конфиденциальности."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                SELECT user_consent
                FROM users
                WHERE user_id = %s;
            ''', (user_id,))
            result = cursor.fetchone()
            return result[0] if result else False

def set_user_subscription(user_id, subscription_type):
    """Установка типа подписки для пользователя."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                UPDATE users
                SET subscription_type = %s
                WHERE user_id = %s;
            ''', (subscription_type, user_id))
            conn.commit()

def delete_user(user_id):
    """Удаление пользователя из базы данных."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                DELETE FROM users
                WHERE user_id = %s;
            ''', (user_id,))
            conn.commit()

def block_user(user_id):
    """Блокировка пользователя."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                UPDATE users
                SET is_blocked = TRUE
                WHERE user_id = %s;
            ''', (user_id,))
            conn.commit()

def get_user_profile_by_username(username):
    """Получение профиля пользователя по username."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                SELECT username, subscription_type, generated_links, is_admin, is_blocked, user_consent
                FROM users
                WHERE username = %s;
            ''', (username,))
            return cursor.fetchone()

def get_user_subscription(user_id):
    """Получение типа подписки пользователя по user_id."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                SELECT subscription_type
                FROM users
                WHERE user_id = %s;
            ''', (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None

def get_statistics():
    """Получение статистики по пользователям и ссылкам."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM users;')
            user_count = cursor.fetchone()[0]

            cursor.execute('SELECT SUM(generated_links) FROM users;')
            link_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM users WHERE subscription_type = %s;', ('PAID',))
            active_subscriptions = cursor.fetchone()[0]

            return {
                'user_count': user_count,
                'link_count': link_count,
                'active_subscriptions': active_subscriptions
            }
