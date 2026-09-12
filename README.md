# Job Application Tracker

A complete, production-quality web application to track job applications through a pipeline. Built with Python, Flask, and SQLite.

## Features

- **Dashboard**: Track your pipeline velocity with stats cards and a Chart.js visualization of applications submitted over time.
- **Application Management**: Create, Read, Update, and Delete applications. Add companies on the fly.
- **Offer Management**: Accept a job offer to automatically archive all other active applications. Includes a complete 1-click atomic undo system powered by database snapshots.
- **Interaction Logging**: Keep a timeline of all touchpoints (emails, calls, interviews) for each application.
- **Reminders**: Automatically highlights applications that need follow-up or haven't been updated in 7 days.
- **Search & Filter**: Find applications by company, job title, or current status.
- **CSV Export**: Download all your application data for external analysis.
- **Velocity Tracking**: Automatically logs when an application changes status (e.g., from Applied to Interview).

## Tech Stack

- **Backend**: Python 3.11+, Flask
  - *Justification*: Flask is simple, explicit, and perfect for learning the fundamentals of web development without the "magic" of larger frameworks like Django.
- **Database**: SQLite via SQLAlchemy ORM
  - *Justification*: An ORM abstracts raw SQL into Python objects, preventing SQL injection and making it easy to swap databases (e.g., to PostgreSQL) later.
- **Frontend**: Server-rendered HTML with Jinja2 + Bootstrap 5
  - *Justification*: Clean, responsive design without the overhead of a heavy JavaScript framework. Easy for beginners to read and modify.
- **Charts**: Chart.js
  - *Justification*: Lightweight and easy to integrate with server-rendered data.

## Setup Instructions

1. **Prerequisites**: Ensure you have Python 3.11+ installed.
2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   ```
3. **Activate the Virtual Environment**:
   - Windows: `.\venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Set Environment Variables**:
   Create a `.env` file in the root directory (one is already provided) with:
   ```
   SECRET_KEY=your-secret-key
   DATABASE_URI=sqlite:///job_tracker.db
   ```
6. **Initialize the Database and Seed Dummy Data**:
   ```bash
   python seed.py
   ```
7. **Run the Application**:
   ```bash
   python app.py
   ```
8. Open your browser and navigate to `http://127.0.0.1:5000/`.

## Screenshots

*(Add your screenshots here)*

## What I Learned

*(Leave this blank to fill in later!)*

## how to run this
cd "e:\my_projects\Job Application Tracker"
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python app.py
