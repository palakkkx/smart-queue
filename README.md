# Smart Queue

A web-based **Smart Queue Management System** designed to digitize and simplify queue handling. The system allows users to join a queue, track their position in real time, and receive an updated queue status, while administrators can manage customers and control the serving process.

## 🚀 Features

### 👤 User Features

* Join the queue digitally without standing in a physical line
* Receive a unique queue number
* View current queue status
* Track the number of people ahead in the queue
* Get updated automatically as the queue progresses
* View their queue status through a simple dashboard

### 🔐 Admin Features

* Admin dashboard for queue management
* View all customers currently in the queue
* Start serving the next customer
* Mark customers as completed
* Manage the queue efficiently
* Monitor the current queue status

### ⚡ Smart Queue Management

* Automatic queue numbering
* Real-time queue status updates
* Separate user and admin interfaces
* Queue progression based on serving/completion status
* Simple and responsive web interface

## 🛠️ Tech Stack

**Frontend**

* HTML
* CSS
* JavaScript

**Backend**

* Python
* Flask

**Database**

* SQLite

**Tools**

* Git
* GitHub
* VS Code

## 📂 Project Structure

```text
smart_queue/
│
├── app.py                 # Main Flask application
├── static/
│   └── style.css          # Styling
│
├── templates/             # HTML templates
│   ├── index.html
│   ├── dashboard.html
│   ├── admin.html
│   └── ...
│
├── .gitignore
├── requirements.txt
└── README.md
```

> The exact files and folders may vary depending on the current version of the project.

## 🔄 How It Works

The Smart Queue system follows a simple workflow:

```text
User
  │
  ▼
Join Queue
  │
  ▼
Receive Queue Number
  │
  ▼
Track Queue Status
  │
  ▼
Admin Starts Serving
  │
  ▼
Customer Served
  │
  ▼
Queue Updated
```

### User Flow

1. The user opens the Smart Queue application.
2. The user joins the queue.
3. The system assigns a queue number.
4. The user can view their current queue status.
5. As customers are served, the queue position is updated.

### Admin Flow

1. The administrator opens the admin dashboard.
2. The admin views the active queue.
3. The admin starts serving a customer.
4. After service is completed, the customer is marked as completed.
5. The queue automatically progresses to the next customer.

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/palakkkx/smart-queue.git
```

### 2. Navigate to the project

```bash
cd smart-queue
```

### 3. Create a virtual environment

Mac/Linux:

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

```bash
python app.py
```

The application should start on:

```text
http://127.0.0.1:5000/
```

Open the URL in your browser to use the application.

## 📌 Example Routes

The application contains routes for different queue operations, including:

```text
/dashboard
/admin
/join_queue
/queue_status
/start_serving/<id>
/complete/<id>
```

These routes handle user dashboards, queue joining, queue status tracking, and administrative queue operations.

## 🎯 Use Cases

Smart Queue can be used in environments where customers need to wait for a service, such as:

* 🏥 Hospitals and clinics
* 🏦 Banks
* 🏢 Government offices
* 🍽️ Restaurants
* 🛍️ Service centers
* 🎓 College/University offices
* 🧾 Customer service counters

## 💡 Future Improvements

Possible improvements for future versions include:

* SMS/email notifications when the user's turn is approaching
* Estimated waiting-time calculation
* Multiple service counters
* Priority/VIP queue handling
* User authentication and authorization
* Admin authentication
* Analytics dashboard
* Queue history and reports
* Cloud database integration
* Deployment to a cloud platform
* Mobile-friendly/PWA support

## 📚 Learning Outcomes

Through this project, I worked with:

* Flask-based web application development
* Backend routing and request handling
* Database operations
* CRUD operations
* Queue data structures and queue management logic
* Frontend-backend integration
* HTML/CSS-based UI development
* Git and GitHub version control

## 👩‍💻 Author

**Palak Garg**

B.Tech — Electronics & Instrumentation Engineering

GitHub: https://github.com/palakkkx

---

⭐ If you find this project useful, consider giving the repository a star!
