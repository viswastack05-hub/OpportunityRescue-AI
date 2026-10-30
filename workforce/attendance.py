from workforce.database import get_connection


def mark_check_in(employee_id, attendance_date, check_in, source="Manual"):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT employee_id FROM employees
        WHERE employee_id = ? AND employment_status = 'Active'
    """, (employee_id,))

    employee = cursor.fetchone()

    if not employee:
        conn.close()
        return False, "Active employee not found."

    try:
        cursor.execute("""
            INSERT INTO attendance (
                employee_id, date, check_in, source
            )
            VALUES (?, ?, ?, ?)
        """, (employee_id, attendance_date, check_in, source))

        conn.commit()
        return True, "Check-in recorded successfully!"

    except Exception as e:
        return False, str(e)

    finally:
        conn.close()


def mark_check_out(employee_id, attendance_date, check_out):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE attendance
        SET check_out = ?
        WHERE employee_id = ? AND date = ?
        AND check_out IS NULL
    """, (check_out, employee_id, attendance_date))

    conn.commit()
    updated = cursor.rowcount
    conn.close()

    if updated:
        return True, "Check-out recorded successfully!"

    return False, "No pending check-in found."


def get_attendance(attendance_date):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.employee_id, e.name, e.department,
               a.date, a.check_in, a.check_out, a.source
        FROM attendance a
        JOIN employees e ON a.employee_id = e.employee_id
        WHERE a.date = ?
        ORDER BY a.check_in
    """, (attendance_date,))

    records = cursor.fetchall()
    conn.close()

    return records
from datetime import datetime


def calculate_working_hours(check_in, check_out, break_minutes=60):

    if not check_in or not check_out:
        return None

    start = datetime.strptime(check_in, "%H:%M")
    end = datetime.strptime(check_out, "%H:%M")

    if end <= start:
        return None

    total_minutes = (end - start).total_seconds() / 60
    working_minutes = total_minutes - break_minutes

    if working_minutes < 0:
        return 0

    return round(working_minutes / 60, 2)


def check_attendance_status(check_in, shift_start="09:00",
                            check_out=None, shift_end="18:00"):

    actual_in = datetime.strptime(check_in, "%H:%M")
    expected_in = datetime.strptime(shift_start, "%H:%M")

    late_minutes = max(
        0, int((actual_in - expected_in).total_seconds() / 60)
    )

    early_departure = 0

    if check_out:
        actual_out = datetime.strptime(check_out, "%H:%M")
        expected_out = datetime.strptime(shift_end, "%H:%M")

        early_departure = max(
            0, int((expected_out - actual_out).total_seconds() / 60)
        )

    return {
        "late_minutes": late_minutes,
        "early_departure_minutes": early_departure,
        "status": "Late" if late_minutes > 0 else "On Time"
    }