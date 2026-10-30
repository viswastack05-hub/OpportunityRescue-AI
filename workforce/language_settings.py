import sqlite3
from workforce.database import get_connection


def initialize_language_settings():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_language_preferences (
            user_id TEXT PRIMARY KEY,
            language_code TEXT DEFAULT 'en'
        )
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO company_settings
        (setting_key, setting_value)
        VALUES ('default_language', 'en')
    """)

    conn.commit()
    conn.close()


def get_company_language():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT setting_value
        FROM company_settings
        WHERE setting_key = 'default_language'
    """)

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else "en"


def set_company_language(language_code):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE company_settings
        SET setting_value = ?
        WHERE setting_key = 'default_language'
    """, (language_code,))

    conn.commit()
    conn.close()


def get_user_language(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT language_code
        FROM user_language_preferences
        WHERE user_id = ?
    """, (user_id,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else get_company_language()


def set_user_language(user_id, language_code):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO user_language_preferences
        (user_id, language_code)
        VALUES (?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET language_code = excluded.language_code
    """, (user_id, language_code))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialize_language_settings()
    print("Language settings database initialized!")