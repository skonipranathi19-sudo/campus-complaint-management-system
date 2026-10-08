from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from config import DB_CONFIG

app = Flask(__name__)
app.secret_key = "change-this-secret-key-in-production"


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("You are not authorized to access that page.", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "danger")
            return render_template("register.html")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("An account with this email already exists.", "danger")
                return render_template("register.html")

            password_hash = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, 'student')",
                (name, email, password_hash)
            )
            conn.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except Error as e:
            flash(f"Database error: {e}", "danger")
        finally:
            if "cursor" in locals():
                cursor.close()
            if "conn" in locals() and conn.is_connected():
                conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, name, email, password_hash, role FROM users WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()

            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                session["name"] = user["name"]
                session["role"] = user["role"]
                flash("Login successful.", "success")
                return redirect(url_for("dashboard"))

            flash("Invalid email or password.", "danger")
        except Error as e:
            flash(f"Database error: {e}", "danger")
        finally:
            if "cursor" in locals():
                cursor.close()
            if "conn" in locals() and conn.is_connected():
                conn.close()

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required()
def dashboard():
    if session["role"] == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("student_dashboard"))


@app.route("/student/dashboard")
@login_required("student")
def student_dashboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT id, category, description, priority, status, created_at
               FROM complaints WHERE user_id = %s
               ORDER BY created_at DESC""",
            (session["user_id"],)
        )
        complaints = cursor.fetchall()
        return render_template("student_dashboard.html", complaints=complaints)
    except Error as e:
        flash(f"Database error: {e}", "danger")
        return render_template("student_dashboard.html", complaints=[])
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals() and conn.is_connected():
            conn.close()


@app.route("/complaint/new", methods=["GET", "POST"])
@login_required("student")
def new_complaint():
    categories = [
        "Water Leakage", "Damaged Light", "Broken Desk",
        "Wi-Fi Issue", "Washroom Problem", "Electrical Issue",
        "Cleanliness", "Other"
    ]

    if request.method == "POST":
        category = request.form.get("category", "")
        description = request.form.get("description", "").strip()

        if category not in categories or not description:
            flash("Please select a category and enter a description.", "danger")
            return render_template("submit_complaint.html", categories=categories)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO complaints
                   (user_id, category, description, priority, status)
                   VALUES (%s, %s, %s, 'Medium', 'Pending')""",
                (session["user_id"], category, description)
            )
            complaint_id = cursor.lastrowid

            cursor.execute(
                """INSERT INTO complaint_history
                   (complaint_id, changed_by, action, old_value, new_value)
                   VALUES (%s, %s, 'Complaint Created', NULL, 'Pending')""",
                (complaint_id, session["user_id"])
            )
            conn.commit()
            flash("Complaint submitted successfully.", "success")
            return redirect(url_for("student_dashboard"))
        except Error as e:
            flash(f"Database error: {e}", "danger")
        finally:
            if "cursor" in locals():
                cursor.close()
            if "conn" in locals() and conn.is_connected():
                conn.close()

    return render_template("submit_complaint.html", categories=categories)


@app.route("/student/complaint/<int:complaint_id>")
@login_required("student")
def student_complaint_details(complaint_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT c.*, u.name AS student_name, u.email
               FROM complaints c
               JOIN users u ON c.user_id = u.id
               WHERE c.id = %s AND c.user_id = %s""",
            (complaint_id, session["user_id"])
        )
        complaint = cursor.fetchone()

        if not complaint:
            flash("Complaint not found.", "danger")
            return redirect(url_for("student_dashboard"))

        cursor.execute(
            """SELECT h.*, u.name AS changed_by_name
               FROM complaint_history h
               JOIN users u ON h.changed_by = u.id
               WHERE h.complaint_id = %s
               ORDER BY h.changed_at DESC""",
            (complaint_id,)
        )
        history = cursor.fetchall()
        return render_template("complaint_details.html", complaint=complaint, history=history, student_view=True)
    except Error as e:
        flash(f"Database error: {e}", "danger")
        return redirect(url_for("student_dashboard"))
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals() and conn.is_connected():
            conn.close()


@app.route("/admin/dashboard")
@login_required("admin")
def admin_dashboard():
    status = request.args.get("status", "")
    category = request.args.get("category", "")

    query = """
        SELECT c.id, c.category, c.description, c.priority, c.status,
               c.created_at, u.name AS student_name, u.email
        FROM complaints c
        JOIN users u ON c.user_id = u.id
        WHERE 1=1
    """
    params = []

    if status:
        query += " AND c.status = %s"
        params.append(status)

    if category:
        query += " AND c.category = %s"
        params.append(category)

    query += " ORDER BY c.created_at DESC"

    categories = [
        "Water Leakage", "Damaged Light", "Broken Desk",
        "Wi-Fi Issue", "Washroom Problem", "Electrical Issue",
        "Cleanliness", "Other"
    ]

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, tuple(params))
        complaints = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) AS total FROM complaints")
        total = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM complaints WHERE status='Pending'")
        pending = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM complaints WHERE status='In Progress'")
        in_progress = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM complaints WHERE status='Resolved'")
        resolved = cursor.fetchone()["total"]

        stats = {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "resolved": resolved
        }
        return render_template(
            "admin_dashboard.html",
            complaints=complaints,
            categories=categories,
            stats=stats,
            selected_status=status,
            selected_category=category
        )
    except Error as e:
        flash(f"Database error: {e}", "danger")
        return render_template(
            "admin_dashboard.html", complaints=[], categories=categories,
            stats={"total": 0, "pending": 0, "in_progress": 0, "resolved": 0},
            selected_status=status, selected_category=category
        )
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals() and conn.is_connected():
            conn.close()


@app.route("/admin/complaint/<int:complaint_id>")
@login_required("admin")
def admin_complaint_details(complaint_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT c.*, u.name AS student_name, u.email
               FROM complaints c
               JOIN users u ON c.user_id = u.id
               WHERE c.id = %s""",
            (complaint_id,)
        )
        complaint = cursor.fetchone()

        if not complaint:
            flash("Complaint not found.", "danger")
            return redirect(url_for("admin_dashboard"))

        cursor.execute(
            """SELECT h.*, u.name AS changed_by_name
               FROM complaint_history h
               JOIN users u ON h.changed_by = u.id
               WHERE h.complaint_id = %s
               ORDER BY h.changed_at DESC""",
            (complaint_id,)
        )
        history = cursor.fetchall()
        return render_template("complaint_details.html", complaint=complaint, history=history, student_view=False)
    except Error as e:
        flash(f"Database error: {e}", "danger")
        return redirect(url_for("admin_dashboard"))
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals() and conn.is_connected():
            conn.close()


@app.route("/admin/complaint/<int:complaint_id>/update", methods=["POST"])
@login_required("admin")
def update_complaint(complaint_id):
    new_priority = request.form.get("priority")
    new_status = request.form.get("status")

    valid_priorities = ["Low", "Medium", "High"]
    valid_statuses = ["Pending", "In Progress", "Resolved"]

    if new_priority not in valid_priorities or new_status not in valid_statuses:
        flash("Invalid priority or status.", "danger")
        return redirect(url_for("admin_complaint_details", complaint_id=complaint_id))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT priority, status FROM complaints WHERE id = %s",
            (complaint_id,)
        )
        current = cursor.fetchone()

        if not current:
            flash("Complaint not found.", "danger")
            return redirect(url_for("admin_dashboard"))

        cursor.execute(
            """UPDATE complaints
               SET priority = %s, status = %s, updated_at = CURRENT_TIMESTAMP
               WHERE id = %s""",
            (new_priority, new_status, complaint_id)
        )

        if current["priority"] != new_priority:
            cursor.execute(
                """INSERT INTO complaint_history
                   (complaint_id, changed_by, action, old_value, new_value)
                   VALUES (%s, %s, 'Priority Changed', %s, %s)""",
                (complaint_id, session["user_id"], current["priority"], new_priority)
            )

        if current["status"] != new_status:
            cursor.execute(
                """INSERT INTO complaint_history
                   (complaint_id, changed_by, action, old_value, new_value)
                   VALUES (%s, %s, 'Status Changed', %s, %s)""",
                (complaint_id, session["user_id"], current["status"], new_status)
            )

        conn.commit()
        flash("Complaint updated successfully.", "success")
        return redirect(url_for("admin_complaint_details", complaint_id=complaint_id))
    except Error as e:
        flash(f"Database error: {e}", "danger")
        return redirect(url_for("admin_dashboard"))
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals() and conn.is_connected():
            conn.close()


if __name__ == "__main__":
    app.run(debug=True)
