from workforce.database import get_connection


def add_employee(employee_id, name, department, designation,
                 monthly_salary, joining_date):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO employees (
                employee_id, name, department, designation,
                monthly_salary, joining_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            employee_id, name, department, designation,
            monthly_salary, joining_date
        ))

        conn.commit()
        return True, "Employee added successfully!"

    except Exception as e:
        return False, str(e)

    finally:
        conn.close()


def get_all_employees():

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT employee_id, name, department, designation,
                   monthly_salary, joining_date, employment_status
            FROM employees
            ORDER BY employee_id
        """)

        return cursor.fetchall()

    finally:
        conn.close()


def update_employee_status(employee_id, status):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE employees
        SET employment_status = ?
        WHERE employee_id = ?
    """, (status, employee_id))

    conn.commit()
    updated = cursor.rowcount
    conn.close()

    return updated > 0