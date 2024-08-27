import sqlite3

def create_connection():
    conn = sqlite3.connect('database/support_users.db')
    return conn

def initialize_database():
    """Создает таблицы в базе данных, если они не существуют."""
    conn = create_connection()
    cursor = conn.cursor()

    # Создаем таблицу пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        username TEXT,
        is_operator INTEGER DEFAULT 0
    )
    ''')

    # Создаем таблицу тикетов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER,
        user_id INTEGER,
        operator_id INTEGER,
        status TEXT
    )
    ''')

    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def create_ticket(user_id, question):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tickets (user_id, ticket_id, status) VALUES (?, ?, ?)", (user_id, question, 'new'))
    ticket_id = cursor.lastrowid  # Получаем ID последней вставленной строки
    conn.commit()
    conn.close()
    return ticket_id  # Возвращаем ID тикета

def get_operators():
    """Получает список операторов из базы данных."""
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE is_operator = 1")  # Получаем только операторов
        operators = cursor.fetchall()
        
        # Извлекаем user_id из кортежей и возвращаем список
        operator_ids = [operator[0] for operator in operators]  
        
    except Exception as e:
        print(f"Ошибка при получении операторов: {e}")
        operator_ids = []  # Возвращаем пустой список в случае ошибки

    finally:
        conn.close()  # Закрываем соединение, если оно было открыто

    return operator_ids  # Возвращаем список ID операторов

def assign_ticket_to_operator(ticket_id: int, operator_id: int) -> None:
    """Назначает тикет оператору в базе данных."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tickets SET operator_id = ?, status = 'in_progress' WHERE id = ?", (operator_id, ticket_id))
    conn.commit()
    conn.close()

def close_ticket(ticket_id):
    """Закрывает тикет по его ID."""
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE tickets SET status = 'closed' WHERE id = ?", (ticket_id,))
        conn.commit()
    except Exception as e:
        print(f"Ошибка при закрытии тикета: {e}")
    finally:
        conn.close()

def get_ticket_info(ticket_id):
    """Получает информацию о тикете по его ID."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    ticket_info = cursor.fetchone()  # Получаем информацию о тикете
    conn.close()
    return ticket_info


def get_ticket_by_id(ticket_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    ticket = cursor.fetchone()
    conn.close()
    return ticket

def get_unassigned_tickets():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE status = 'new' AND operator_id IS NULL")
    tickets = cursor.fetchall()
    conn.close()
    return tickets

def get_working_tickets():
    """Получает список тикетов, которые находятся в работе и назначены операторам."""
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tickets WHERE status = 'in_progress'")  # Получаем только рабочие тикеты
        tickets = cursor.fetchall()
        
    except Exception as e:
        print(f"Ошибка при получении рабочих тикетов: {e}")
        tickets = []  # Возвращаем пустой список в случае ошибки

    finally:
        conn.close()  # Закрываем соединение, если оно было открыто

    return tickets  # Возвращаем список тикетов

def get_open_ticket(user_id):
    """Получает открытые тикеты для пользователя с статусами 'in_progress' или 'new'."""
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tickets WHERE user_id = ? AND status IN ('in_progress', 'new')", 
            (user_id,)
        )
        ticket = cursor.fetchone()  # Получаем только один открытый тикет
        
    except Exception as e:
        print(f"Ошибка при получении открытого тикета: {e}")
        ticket = None  # Возвращаем None в случае ошибки

    finally:
        conn.close()  # Закрываем соединение, если оно было открыто

    return ticket  # Возвращаем тикет или None