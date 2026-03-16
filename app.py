import sqlite3
from flask import Flask, request, jsonify, abort

app = Flask(__name__)
DATABASE = 'database.db'

def get_db():
    """Создаёт соединение с SQLite и настраивает возврат строк как словари."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Инициализирует таблицы, если их ещё нет."""
    db = get_db()
    cursor = db.cursor()
    # Таблица для одной записи события (принудительно только id=1)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            content TEXT NOT NULL
        )
    ''')
    # Таблица для списка сообщений (до 100 записей)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL
        )
    ''')
    db.commit()
    db.close()

# Инициализация базы данных при старте приложения
with app.app_context():
    init_db()

@app.route('/change_event', methods=['POST'])
def change_event():
    """
    Принимает JSON с полем 'text' (до 300 символов).
    Сохраняет или обновляет единственную запись в таблице event.
    """
    data = request.get_json()
    if not data or 'text' not in data:
        abort(400, description="Missing 'text' parameter")
    text = data['text']
    if len(text) > 300:
        abort(400, description="Text too long, max 300 characters")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM event WHERE id = 1")
    row = cursor.fetchone()

    if row:
        cursor.execute("UPDATE event SET content = ? WHERE id = 1", (text,))
    else:
        cursor.execute("INSERT INTO event (id, content) VALUES (1, ?)", (text,))

    db.commit()
    db.close()
    return jsonify({"status": "ok", "message": "Event updated"})

@app.route('/get_event', methods=['GET'])
def get_event():
    """Возвращает текст из таблицы event или пустую строку, если записи нет."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT content FROM event WHERE id = 1")
    row = cursor.fetchone()
    db.close()
    if row:
        return row['content']
    return ""

@app.route('/writeme', methods=['POST'])
def writeme():
    """
    Принимает JSON с полем 'text' (до 50 символов).
    Добавляет запись в таблицу messages, если там меньше 100 записей.
    """
    data = request.get_json()
    if not data or 'text' not in data:
        abort(400, description="Missing 'text' parameter")
    text = data['text']
    if len(text) > 50:
        abort(400, description="Text too long, max 50 characters")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM messages")
    count = cursor.fetchone()['cnt']
    if count >= 100:
        db.close()
        abort(400, description="Message limit reached (max 100)")

    cursor.execute("INSERT INTO messages (text) VALUES (?)", (text,))
    db.commit()
    db.close()
    return jsonify({"status": "ok", "message": "Message added"})

@app.route('/deleteme', methods=['POST'])
def deleteme():
    """
    Принимает JSON с полем 'text' (до 50 символов).
    Удаляет все записи из messages с точно таким же текстом.
    """
    data = request.get_json()
    if not data or 'text' not in data:
        abort(400, description="Missing 'text' parameter")
    text = data['text']
    if len(text) > 50:
        abort(400, description="Text too long, max 50 characters")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM messages WHERE text = ?", (text,))
    deleted = cursor.rowcount
    db.commit()
    db.close()
    return jsonify({"status": "ok", "message": f"Deleted {deleted} records"})

@app.route('/clearlist', methods=['POST'])
def clearlist():
    """Удаляет все записи из таблицы messages."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM messages")
    db.commit()
    db.close()
    return jsonify({"status": "ok", "message": "All messages cleared"})

@app.route('/getlist', methods=['GET'])
def getlist():
    """Возвращает все записи из таблицы messages в виде JSON-массива."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT text FROM messages ORDER BY id")
    rows = cursor.fetchall()
    db.close()
    messages = [row['text'] for row in rows]
    return jsonify(messages)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8001)
