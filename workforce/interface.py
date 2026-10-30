
import streamlit as st
from datetime import date, datetime

from workforce.database import initialize_database
from workforce.employees import (
    add_employee,
    get_all_employees,
    update_employee_status
)
from workforce.attendance import (
    mark_check_in,
    mark_check_out,
    get_attendance,
    calculate_working_hours,
    check_attendance_status
)
from workforce.translations import translate, LANGUAGE_NAMES


st.set_page_config(
    page_title="OpportunityRescue AI",
    page_icon="👥",
    layout="wide"
)


def show_workforce_dashboard():

    initialize_database()

    # LANGUAGE SELECTION
    if "selected_language" not in st.session_state:
        st.session_state.selected_language = "en"

    selected_language = st.selectbox(
        "🌐 Select Language / மொழியைத் தேர்ந்தெடுக்கவும்",
        options=list(LANGUAGE_NAMES.keys()),
        format_func=lambda code: LANGUAGE_NAMES[code],
        key="selected_language"
    )

    def t(key):
        return translate(key, selected_language)

    st.title("👥 " + t("workforce"))
    st.caption(t("app_name"))

    employee_tab, attendance_tab = st.tabs([
        "👤 " + t("employee_management"),
        "🕒 " + t("attendance_management")
    ])

    # =================================
    # EMPLOYEE MANAGEMENT
    # =================================

    with employee_tab:

        st.subheader(t("add_employee"))

        with st.form("employee_registration"):

            col1, col2 = st.columns(2)

            with col1:
                employee_id = st.text_input(t("employee_id"))
                name = st.text_input(t("employee_name"))
                department = st.text_input(t("department"))

            with col2:
                designation = st.text_input(t("designation"))

                salary = st.number_input(
                    t("monthly_salary") + " (₹)",
                    min_value=0.0,
                    step=1000.0
                )

                joining_date = st.date_input(
                    t("joining_date"),
                    value=date.today()
                )

            submitted = st.form_submit_button(
                t("add_employee"),
                use_container_width=True
            )

            if submitted:

                if not employee_id.strip() or not name.strip() or salary <= 0:

                    st.warning("Please enter Employee ID, Name and Salary.")

                else:

                    success, message = add_employee(
                        employee_id.strip(),
                        name.strip(),
                        department.strip(),
                        designation.strip(),
                        salary,
                        str(joining_date)
                    )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

        st.divider()

        st.subheader(t("employee_directory"))

        employees = get_all_employees()

        if employees:

            st.metric(
                t("employee_directory"),
                len(employees)
            )

            st.dataframe(
                [
                    {
                        t("employee_id"): row[0],
                        t("employee_name"): row[1],
                        t("department"): row[2],
                        t("designation"): row[3],
                        t("monthly_salary"): row[4],
                        t("joining_date"): row[5],
                        t("status"): t(row[6].lower())
                    }
                    for row in employees
                ],
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            st.subheader(t("status"))

            selected_id = st.selectbox(
                t("employee_id"),
                [row[0] for row in employees]
            )

            new_status = st.selectbox(
                t("status"),
                ["Active", "Inactive"],
                format_func=lambda value: t(value.lower())
            )

            if st.button(t("status")):

                success = update_employee_status(
                    selected_id,
                    new_status
                )

                if success:
                    st.success("Employee status updated!")
                    st.rerun()
                else:
                    st.error("Employee not found.")

        else:

            st.info("No employee records available.")

    # =================================
    # ATTENDANCE MANAGEMENT
    # =================================

    with attendance_tab:

        st.subheader(t("attendance_management"))

        employees = get_all_employees()

        active_employees = [
            row for row in employees
            if row[6] == "Active"
        ]

        if not active_employees:

            st.warning("Please add an active employee first.")

        else:

            employee_options = {
                f"{row[0]} - {row[1]}": row[0]
                for row in active_employees
            }

            selected_employee = st.selectbox(
                t("employee_name"),
                list(employee_options.keys())
            )

            selected_id = employee_options[selected_employee]

            attendance_date = st.date_input(
                t("attendance_date"),
                value=date.today()
            )

            attendance_time = st.time_input(
                "Time",
                value=datetime.now().time().replace(
                    second=0,
                    microsecond=0
                )
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "🟢 " + t("check_in"),
                    use_container_width=True
                ):

                    success, message = mark_check_in(
                        selected_id,
                        str(attendance_date),
                        attendance_time.strftime("%H:%M"),
                        "Manual"
                    )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

            with col2:

                if st.button(
                    "🔴 " + t("check_out"),
                    use_container_width=True
                ):

                    success, message = mark_check_out(
                        selected_id,
                        str(attendance_date),
                        attendance_time.strftime("%H:%M")
                    )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

        st.divider()

        st.subheader(t("attendance_records"))

        report_date = st.date_input(
            t("attendance_date"),
            value=date.today(),
            key="attendance_report_date"
        )

        records = get_attendance(str(report_date))

        if records:

            attendance_display = []

            for row in records:

                employee_id, name, department, record_date, check_in, check_out, source = row

                hours = calculate_working_hours(
                    check_in,
                    check_out
                )

                attendance_status = check_attendance_status(
                    check_in
                )["status"]

                translated_status = (
                    t("late_arrival")
                    if attendance_status == "Late"
                    else t("on_time")
                )

                attendance_display.append({
                    t("employee_id"): employee_id,
                    t("employee_name"): name,
                    t("department"): department,
                    t("attendance_date"): record_date,
                    t("check_in"): check_in,
                    t("check_out"): check_out or "Pending",
                    t("working_hours"): (
                        hours if hours is not None else "Pending"
                    ),
                    t("status"): translated_status,
                    "Source": source
                })

            st.dataframe(
                attendance_display,
                use_container_width=True,
                hide_index=True
            )

            col1, col2 = st.columns(2)

            col1.metric(
                "Employees Present",
                len(records)
            )

            col2.metric(
                "Completed Check-outs",
                sum(1 for row in records if row[5])
            )

        else:

            st.info("No attendance records found for this date.")


if __name__ == "__main__":
    show_workforce_dashboard()
