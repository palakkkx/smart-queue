import sqlite3
import pickle

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

from datetime import datetime


DATABASE = "database/queue.db"
MODEL_FILE = "queue_model.pkl"


# ==================================================
# CONNECT TO DATABASE
# ==================================================

connection = sqlite3.connect(DATABASE)
connection.row_factory = sqlite3.Row


# ==================================================
# GET COMPLETED QUEUES
# ==================================================

rows = connection.execute("""
    SELECT
        service,
        joined_at,
        service_duration,
        counter
    FROM queue
    WHERE status = 'Completed'
    AND service_duration IS NOT NULL
    AND service_duration BETWEEN 1 AND 60
""").fetchall()


connection.close()


# ==================================================
# CHECK TRAINING DATA
# ==================================================

if len(rows) < 5:

    print("Not enough valid historical records.")
    print("Complete at least 5 realistic queues.")

    exit()


print()
print("================================")
print("SMART QUEUE ML TRAINING")
print("================================")
print()
print("Valid training records:", len(rows))


# ==================================================
# PREPARE DATA
# ==================================================

services = []
hours = []
days = []
counters = []
people_ahead_values = []
targets = []


# Connect again to calculate people ahead
connection = sqlite3.connect(DATABASE)
connection.row_factory = sqlite3.Row


for row in rows:

    joined_time = datetime.strptime(
        row["joined_at"],
        "%Y-%m-%d %H:%M:%S"
    )


    service = row["service"]

    counter = row["counter"]

    joined_at = row["joined_at"]


    # ----------------------------------------------
    # PEOPLE AHEAD AT JOIN TIME
    # ----------------------------------------------

    people_result = connection.execute("""
        SELECT COUNT(*) AS count

        FROM queue

        WHERE service = ?

        AND counter = ?

        AND id < (
            SELECT id
            FROM queue
            WHERE service = ?
            AND counter = ?
            AND joined_at = ?
            LIMIT 1
        )
    """, (
        service,
        counter,
        service,
        counter,
        joined_at
    )).fetchone()


    people_ahead = people_result["count"]


    # ----------------------------------------------
    # FEATURES
    # ----------------------------------------------

    services.append(service)

    hours.append(
        joined_time.hour
    )

    days.append(
        joined_time.weekday()
    )

    counters.append(
        counter
    )

    people_ahead_values.append(
        people_ahead
    )


    # ----------------------------------------------
    # TARGET
    # ----------------------------------------------

    targets.append(
        float(row["service_duration"])
    )


connection.close()


# ==================================================
# ENCODE SERVICE
# ==================================================

encoder = LabelEncoder()

service_encoded = encoder.fit_transform(
    services
)


# ==================================================
# CREATE ML FEATURES
# ==================================================

X = []


for i in range(len(targets)):

    X.append([

        service_encoded[i],

        hours[i],

        days[i],

        counters[i],

        people_ahead_values[i]

    ])


y = targets


# ==================================================
# TRAIN RANDOM FOREST
# ==================================================

model = RandomForestRegressor(

    n_estimators=150,

    random_state=42,

    max_depth=8

)


model.fit(
    X,
    y
)


# ==================================================
# SAVE MODEL
# ==================================================

model_data = {

    "model": model,

    "encoder": encoder,

    "features": [
        "service",
        "hour",
        "day",
        "counter",
        "people_ahead"
    ]

}


with open(
    MODEL_FILE,
    "wb"
) as file:

    pickle.dump(
        model_data,
        file
    )


# ==================================================
# TRAINING SUMMARY
# ==================================================

print()

print("Features used:")
print("1. Service type")
print("2. Time of day")
print("3. Day of week")
print("4. Counter number")
print("5. People ahead")

print()

print(
    "Training records:",
    len(targets)
)

print()

print("Model trained successfully!")

print(
    "Saved as:",
    MODEL_FILE
)

print()

print("================================")