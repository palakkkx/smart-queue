from flask import Flask, render_template, request, redirect, session
import sqlite3
import pickle
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "smart_queue_secret_key"

DATABASE = "database/queue.db"
MODEL_FILE = "queue_model.pkl"

NUMBER_OF_COUNTERS = 3


# ==================================================
# DATABASE
# ==================================================

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():

    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    try:
        connection.execute("""
            ALTER TABLE users
            ADD COLUMN role TEXT NOT NULL DEFAULT 'user'
        """)
    except sqlite3.OperationalError:
        pass

    connection.execute("""
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            service TEXT NOT NULL,
            queue_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Waiting',
            joined_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    try:
        connection.execute("""
            ALTER TABLE queue
            ADD COLUMN completed_at TEXT
        """)
    except sqlite3.OperationalError:
        pass

    try:
        connection.execute("""
            ALTER TABLE queue
            ADD COLUMN service_duration REAL
        """)
    except sqlite3.OperationalError:
        pass

    try:
        connection.execute("""
            ALTER TABLE queue
            ADD COLUMN counter INTEGER NOT NULL DEFAULT 1
        """)
    except sqlite3.OperationalError:
        pass

    connection.commit()
    connection.close()


# ==================================================
# LOAD ML MODEL
# ==================================================

def load_model():

    try:

        with open(MODEL_FILE, "rb") as file:
            model_data = pickle.load(file)

        return (
            model_data["model"],
            model_data["encoder"]
        )

    except Exception:

        return None, None


ml_model, service_encoder = load_model()


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():
    return render_template("login.html")


# ==================================================
# REGISTER
# ==================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        connection = get_db_connection()

        try:

            connection.execute("""
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
            """, (
                name,
                email,
                hashed_password
            ))

            connection.commit()

        except sqlite3.IntegrityError:

            connection.close()

            return "Email already registered. Please use another email."

        connection.close()

        return redirect("/")

    return render_template("register.html")


# ==================================================
# LOGIN
# ==================================================

@app.route("/login", methods=["POST"])
def login():

    email = request.form["email"]
    password = request.form["password"]

    connection = get_db_connection()

    user = connection.execute("""
        SELECT *
        FROM users
        WHERE email = ?
    """, (
        email,
    )).fetchone()

    connection.close()

    if user and check_password_hash(
        user["password"],
        password
    ):

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["role"] = user["role"]

        if user["role"] == "admin":
            return redirect("/admin")

        return redirect("/dashboard")

    return "Invalid email or password. Please try again."


# ==================================================
# DASHBOARD
# ==================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/")

    connection = get_db_connection()

    active_queue = connection.execute("""
        SELECT *
        FROM queue
        WHERE user_id = ?
        AND status IN ('Waiting', 'Serving')
        ORDER BY id DESC
        LIMIT 1
    """, (
        session["user_id"],
    )).fetchone()

    connection.close()

    return render_template(
        "dashboard.html",
        name=session["user_name"],
        active_queue=active_queue
    )


# ==================================================
# JOIN QUEUE
# ==================================================

@app.route("/join_queue", methods=["POST"])
def join_queue():

    if "user_id" not in session:
        return redirect("/")

    service = request.form["service"]

    connection = get_db_connection()

    existing_queue = connection.execute("""
        SELECT id
        FROM queue
        WHERE user_id = ?
        AND status IN ('Waiting', 'Serving')
    """, (
        session["user_id"],
    )).fetchone()

    if existing_queue:

        connection.close()

        return redirect("/queue_status")


    result = connection.execute("""
        SELECT MAX(queue_number) AS max_number
        FROM queue
        WHERE service = ?
    """, (
        service,
    )).fetchone()

    if result["max_number"] is None:

        queue_number = 1

    else:

        queue_number = result["max_number"] + 1


    # Smart counter assignment
    counter_counts = {}

    for counter_number in range(
        1,
        NUMBER_OF_COUNTERS + 1
    ):

        result = connection.execute("""
            SELECT COUNT(*) AS count
            FROM queue
            WHERE service = ?
            AND counter = ?
            AND status IN ('Waiting', 'Serving')
        """, (
            service,
            counter_number
        )).fetchone()

        counter_counts[counter_number] = result["count"]


    assigned_counter = min(
        counter_counts,
        key=counter_counts.get
    )


    joined_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    connection.execute("""
        INSERT INTO queue
        (
            user_id,
            service,
            queue_number,
            status,
            joined_at,
            counter
        )
        VALUES (?, ?, ?, 'Waiting', ?, ?)
    """, (
        session["user_id"],
        service,
        queue_number,
        joined_at,
        assigned_counter
    ))

    connection.commit()
    connection.close()

    return redirect("/queue_status")


# ==================================================
# QUEUE STATUS + IMPROVED ML
# ==================================================

@app.route("/queue_status")
def queue_status():

    if "user_id" not in session:
        return redirect("/")


    connection = get_db_connection()

    current_queue = connection.execute("""
        SELECT *
        FROM queue
        WHERE user_id = ?
        AND status IN ('Waiting', 'Serving')
        ORDER BY id DESC
        LIMIT 1
    """, (
        session["user_id"],
    )).fetchone()


    if current_queue:

        # ------------------------------------------
        # PEOPLE AHEAD
        # ------------------------------------------

        if current_queue["status"] == "Serving":

            people_ahead = 0

        else:

            people_ahead = connection.execute("""
                SELECT COUNT(*) AS count
                FROM queue
                WHERE service = ?
                AND counter = ?
                AND queue_number < ?
                AND status IN ('Waiting', 'Serving')
            """, (
                current_queue["service"],
                current_queue["counter"],
                current_queue["queue_number"]
            )).fetchone()["count"]


        # ------------------------------------------
        # DEFAULT SERVICE TIMES
        # ------------------------------------------

        default_times = {

            "Bank": 8,
            "Hospital": 10,
            "College Office": 6,
            "Government Office": 10,
            "Cafeteria": 3,
            "Food Court": 4,
            "Coffee Shop": 2,
            "Mess": 5,
            "Juice Counter": 2

        }

        default_time = default_times.get(
            current_queue["service"],
            5
        )


        # ------------------------------------------
        # ML PREDICTION
        # ------------------------------------------

        average_time = default_time
        prediction_method = "Default estimate"


        if (
            ml_model is not None
            and service_encoder is not None
        ):

            try:

                now = datetime.now()

                service = current_queue["service"]

                known_services = list(
                    service_encoder.classes_
                )


                if service in known_services:

                    encoded_service = (
                        service_encoder
                        .transform([service])[0]
                    )


                    hour = now.hour

                    day = now.weekday()

                    counter = current_queue["counter"]


                    # IMPORTANT:
                    # These match the 5 features
                    # used by train_model.py

                    features = [[
                        encoded_service,
                        hour,
                        day,
                        counter,
                        people_ahead
                    ]]


                    predicted_time = ml_model.predict(
                        features
                    )[0]


                    average_time = round(
                        float(predicted_time),
                        1
                    )


                    # Prevent unrealistic values
                    if average_time < 1:
                        average_time = 1

                    if average_time > 60:
                        average_time = 60


                    prediction_method = (
                        "AI / ML prediction"
                    )


            except Exception:

                average_time = default_time

                prediction_method = (
                    "Default estimate"
                )


        # ------------------------------------------
        # WAITING TIME
        # ------------------------------------------

        if current_queue["status"] == "Serving":

            estimated_wait = 0

        else:

            estimated_wait = round(
                people_ahead * average_time
            )


        if estimated_wait > 120:
            estimated_wait = 120


    else:

        people_ahead = 0
        estimated_wait = 0
        average_time = 0
        prediction_method = "No active queue"


    connection.close()


    return render_template(
        "queue_status.html",
        queue=current_queue,
        people_ahead=people_ahead,
        estimated_wait=estimated_wait,
        average_time=average_time,
        prediction_method=prediction_method
    )


# ==================================================
# ADMIN
# ==================================================

@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect("/")

    if session.get("role") != "admin":
        return "Access Denied: Admins only.", 403

    connection = get_db_connection()


    queues = connection.execute("""
        SELECT
            queue.id,
            queue.service,
            queue.queue_number,
            queue.counter,
            queue.status,
            queue.joined_at,
            users.name

        FROM queue

        JOIN users
        ON queue.user_id = users.id

        WHERE queue.status IN ('Waiting', 'Serving')

        ORDER BY
            queue.service,
            queue.counter,
            queue.queue_number
    """).fetchall()


    total_waiting = connection.execute("""
        SELECT COUNT(*)
        FROM queue
        WHERE status = 'Waiting'
    """).fetchone()[0]


    total_serving = connection.execute("""
        SELECT COUNT(*)
        FROM queue
        WHERE status = 'Serving'
    """).fetchone()[0]


    completed_today = connection.execute("""
        SELECT COUNT(*)
        FROM queue
        WHERE status = 'Completed'
        AND date(completed_at) =
            date('now', 'localtime')
    """).fetchone()[0]


    total_completed = connection.execute("""
        SELECT COUNT(*)
        FROM queue
        WHERE status = 'Completed'
    """).fetchone()[0]


    service_counts = connection.execute("""
        SELECT
            service,
            COUNT(*) AS count

        FROM queue

        WHERE status IN ('Waiting', 'Serving')

        GROUP BY service

        ORDER BY count DESC
    """).fetchall()


    average_result = connection.execute("""
        SELECT AVG(service_duration)
        AS average_time

        FROM queue

        WHERE status = 'Completed'

        AND service_duration IS NOT NULL

        AND service_duration BETWEEN 1 AND 60
    """).fetchone()


    if average_result["average_time"] is not None:

        average_service_time = round(
            average_result["average_time"],
            1
        )

    else:

        average_service_time = 0


    if service_counts:

        busiest_service = service_counts[0]["service"]
        busiest_count = service_counts[0]["count"]

    else:

        busiest_service = "None"
        busiest_count = 0


    service_performance = connection.execute("""
        SELECT
            service,
            COUNT(*) AS completed_count,
            ROUND(
                AVG(service_duration),
                1
            ) AS average_time

        FROM queue

        WHERE status = 'Completed'

        AND service_duration IS NOT NULL

        AND service_duration BETWEEN 1 AND 60

        GROUP BY service

        ORDER BY average_time DESC
    """).fetchall()


    counter_load = connection.execute("""
        SELECT
            service,
            counter,

            SUM(
                CASE
                    WHEN status = 'Waiting'
                    THEN 1
                    ELSE 0
                END
            ) AS waiting,

            SUM(
                CASE
                    WHEN status = 'Serving'
                    THEN 1
                    ELSE 0
                END
            ) AS serving

        FROM queue

        WHERE status IN ('Waiting', 'Serving')

        GROUP BY service, counter

        ORDER BY service, counter
    """).fetchall()


    connection.close()


    return render_template(
        "admin.html",
        queues=queues,
        total_waiting=total_waiting,
        total_serving=total_serving,
        completed_today=completed_today,
        total_completed=total_completed,
        service_counts=service_counts,
        average_service_time=average_service_time,
        busiest_service=busiest_service,
        busiest_count=busiest_count,
        service_performance=service_performance,
        counter_load=counter_load
    )


# ==================================================
# START SERVING
# ==================================================

@app.route("/start_serving/<int:queue_id>")
def start_serving(queue_id):

    if "user_id" not in session:
        return redirect("/")

    if session.get("role") != "admin":
        return "Access Denied: Admins only.", 403


    connection = get_db_connection()


    queue = connection.execute("""
        SELECT *
        FROM queue
        WHERE id = ?
    """, (
        queue_id,
    )).fetchone()


    if queue is None:

        connection.close()

        return "Queue not found.", 404


    current_serving = connection.execute("""
        SELECT id
        FROM queue

        WHERE service = ?
        AND counter = ?
        AND status = 'Serving'

        LIMIT 1
    """, (
        queue["service"],
        queue["counter"]
    )).fetchone()


    if current_serving:

        connection.close()

        return (
            "This counter is already serving "
            "another customer."
        )


    connection.execute("""
        UPDATE queue
        SET status = 'Serving'
        WHERE id = ?
    """, (
        queue_id,
    ))


    connection.commit()
    connection.close()


    return redirect("/admin")


# ==================================================
# COMPLETE QUEUE
# ==================================================

@app.route(
    "/complete/<int:queue_id>",
    methods=["GET", "POST"]
)
def complete_queue(queue_id):

    if "user_id" not in session:
        return redirect("/")

    if session.get("role") != "admin":
        return "Access Denied: Admins only.", 403


    connection = get_db_connection()


    queue = connection.execute("""
        SELECT *
        FROM queue
        WHERE id = ?
    """, (
        queue_id,
    )).fetchone()


    if queue is None:

        connection.close()

        return "Queue not found.", 404


    if request.method == "GET":

        connection.close()

        return render_template(
            "complete_queue.html",
            queue=queue
        )


    duration_text = request.form.get(
        "service_duration"
    )


    try:

        service_duration = float(
            duration_text
        )

    except (ValueError, TypeError):

        connection.close()

        return "Please enter a valid service time."


    if (
        service_duration < 1
        or service_duration > 60
    ):

        connection.close()

        return (
            "Service time must be between "
            "1 and 60 minutes."
        )


    completed_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    connection.execute("""
        UPDATE queue

        SET
            status = 'Completed',
            completed_at = ?,
            service_duration = ?

        WHERE id = ?
    """, (
        completed_at,
        service_duration,
        queue_id
    ))


    connection.commit()
    connection.close()


    return redirect("/admin")


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ==================================================
# START
# ==================================================

if __name__ == "__main__":

    create_database()

    app.run(debug=True)