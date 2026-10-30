import sqlite3
import os

DB_PATH = os.path.join("data", "workforce.db")


def get_connection():
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_PATH)


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT,
            designation TEXT,
            monthly_salary REAL NOT NULL,
            joining_date TEXT,
            employment_status TEXT DEFAULT 'Active'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            date TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            source TEXT DEFAULT 'Manual',
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
            UNIQUE(employee_id, date)
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialize_database()
    print("Workforce database initialized successfully!")