# Code Walkthrough: Job Application Tracker

This document explains the architecture and code line-by-line so you can study it and explain it in a technical interview.

## 1. Architecture Pattern: The Application Factory (`app.py`)

Instead of creating `app = Flask(__name__)` globally at the top of a file, we wrap it in `def create_app()`.
**Why?** This is the **Application Factory Pattern**. It prevents circular imports (where `routes.py` imports `app.py` and `app.py` imports `routes.py`) and allows you to create multiple instances of the app with different configurations (e.g., a test database for automated testing).

## 2. Configuration Management (`config.py` & `.env`)

We use `python-dotenv` to load secrets from a `.env` file into `os.environ`.
**Why?** You should never hardcode passwords or secret keys in your source code. `config.py` acts as a central place to map these environment variables into a Python class that Flask can consume via `app.config.from_object()`.

## 3. Database & Models (`models.py`)

We use **SQLAlchemy**, an Object-Relational Mapper (ORM).
- **Classes = Tables**: Each class (e.g., `Company`) represents a table.
- **Attributes = Columns**: `id = db.Column(...)` represents a column.
- **Relationships**: `db.relationship` tells SQLAlchemy how tables connect. We use a **One-to-Many** relationship: One `Company` can have many `Application`s. The `company_id = db.Column(db.ForeignKey('company.id'))` enforces referential integrity.
- **Indices**: We added `index=True` to fields like `job_title` and `status`. An index is like a book's index—it makes searching much faster because the database doesn't have to scan every single row.

### The SQLAlchemy Event Listener
At the bottom of `models.py`, there is an `@event.listens_for(Application.status, 'set')` function.
**Why?** This is a database trigger implemented in Python. Instead of remembering to manually log a history record every time we update an application's status in our routes, this listener automatically watches the `status` field. If it changes, it inserts a new `StatusHistory` record. This guarantees our velocity metrics are always accurate.

## 4. Business Logic vs. Controllers (`services.py` & `routes.py`)

- **`routes.py` (Controllers)**: Handles the HTTP requests (GET/POST), validates forms, and returns HTML templates. It uses **Blueprints** (`bp = Blueprint(...)`) to organize routes, making the app scalable.
- **`services.py` (Business Logic)**: Contains complex calculations, like finding apps that need attention or grouping data for Chart.js.
**Why separate them?** "Separation of Concerns". If you want to build a mobile app later and need a JSON API, you can reuse `services.py` without rewriting the logic currently trapped inside HTML route handlers.

## 5. Forms & Security (`forms.py`)

We use **Flask-WTF**. It automatically generates HTML form fields and provides server-side validation.
Crucially, it includes **CSRF Protection** (Cross-Site Request Forgery). Every form includes a hidden token (`{{ form.hidden_tag() }}`). This ensures that when a POST request is made to delete or update data, it originated from *your* app, not a malicious third-party site tricking your browser.

## 6. Frontend (`templates/` & Bootstrap)

We use **Jinja2** templating. `base.html` contains the skeleton (navbar, CSS links), and other pages use `{% extends 'base.html' %}` to fill in the `{% block content %}`. This DRY (Don't Repeat Yourself) approach means you only write the navbar once.

## 7. The "Accept Offer" Flow (Advanced Backend Concepts)

The "Accept Offer" feature introduces advanced data management patterns to ensure safety and reliability.

### What is a Database Transaction?
A database transaction groups multiple SQL operations into a single logical unit of work. Transactions follow the **ACID** properties (Atomicity, Consistency, Isolation, Durability). We use `db.session.commit()` to finalize a transaction, and `db.session.rollback()` to cancel it.

### Atomicity
Atomicity guarantees that a transaction is "all or nothing." When you accept an offer, the system must:
1. Mark the target application as "Accepted".
2. Mark all other active applications as "Archived".
3. Save snapshots of the previous states.
If step 3 fails (e.g., due to a database constraint), Atomicity ensures steps 1 and 2 are rolled back. You never end up in a corrupted state where an offer is accepted but other applications aren't archived.

### Idempotency
An operation is idempotent if doing it once has the same effect as doing it multiple times. In `services.py`, the `accept_offer_transaction` function first checks `if get_current_accepted_offer():`. If a user accidentally double-clicks the "Accept Offer" button, the second request safely aborts rather than throwing errors or corrupting the snapshot table.

### Soft-Delete vs. Hard-Delete
When an offer is accepted, we don't *delete* the other applications (`db.session.delete()`). Instead, we change their status to `"Archived"`. This is a form of **soft-deletion**. It removes the items from the main UI (like the dashboard) but preserves the user's historical data, allowing for safe recovery.

### The Snapshot Pattern
To allow a 1-click "Undo" of accepting an offer, we use the **Snapshot Pattern**. Before modifying any application, we save its current status to the `ArchiveSnapshot` table. If the user clicks "Undo", we read from this table to perfectly restore every application to its exact prior state, and then delete the snapshots. Crucially, the rollback logic checks if an archived application was *manually* modified by the user after being archived; if so, it respects the user's manual edit and doesn't overwrite it.

---

## Top 13 Interview Questions to Expect

1. **Why did you use the Application Factory pattern instead of a global app instance?**
   *Answer*: It prevents circular imports and makes unit testing easier because I can spin up a temporary app instance with a test database configuration.

2. **What is an ORM and why use SQLAlchemy instead of raw SQL?**
   *Answer*: An ORM maps database tables to Python objects. It abstracts away dialect-specific SQL, protects against SQL injection automatically through parameterized queries, and makes the code more Pythonic and maintainable.

3. **Explain the relationships in your database.**
   *Answer*: I used a One-to-Many relationship between Company and Application. A foreign key (`company_id`) in the Application table points to the primary key of the Company table, ensuring data integrity (an app can't belong to a non-existent company).

4. **Why did you add indices to specific columns?**
   *Answer*: I added indices to columns frequently used in `WHERE` clauses, like `status` and `job_title`. Indices speed up read operations (filtering/searching) at the slight cost of slower write operations and increased storage.

5. **How did you implement the Status History tracking?**
   *Answer*: I used SQLAlchemy event listeners (`@listens_for`). It intercepts the 'set' event on the `Application.status` attribute and automatically creates a `StatusHistory` record if the value changed. This keeps the route logic clean and guarantees changes are never missed.

6. **What is a Flask Blueprint?**
   *Answer*: Blueprints are a way to organize a Flask application into distinct components. Even though this app is small, using a blueprint for the main routes prepares the app to scale (e.g., adding an `api` blueprint or `auth` blueprint later).

7. **Why do you have a `services.py` file?**
   *Answer*: To maintain Separation of Concerns. The routes should only handle HTTP logic (request parsing, form validation, returning templates). Business logic and complex database queries belong in a service layer, making them reusable and easier to unit test independently of the web framework.

8. **How does Flask-WTF protect against CSRF attacks?**
   *Answer*: It requires a `SECRET_KEY` to generate a unique, cryptographically signed token embedded in a hidden field in the HTML form. When the form is submitted, the server verifies the token matches the user's session, ensuring the request was intentionally made from our site.

9. **Why did you use a POST request for deletions instead of a simple GET link?**
   *Answer*: GET requests are designed to be safe and idempotent. If I used a GET link for deletion (e.g., `/delete/1`), a web crawler (like Googlebot) or browser pre-fetching could visit that link and accidentally delete data. POST requests require explicit user action.

10. **How did you build the dashboard chart without a frontend framework like React?**
    *Answer*: I calculated the data points (applications per week) on the backend in `services.py`, passed the data to the Jinja template, and used the `|tojson` Jinja filter to securely inject it into a native JavaScript `<script>` block that initializes Chart.js.

11. **What does it mean for a database transaction to be "Atomic"? Give an example from this project.**
    *Answer*: Atomicity means "all or nothing." In the Accept Offer feature, changing one application to "Accepted", snapshotting the others, and changing them to "Archived" all happen in one transaction. If the database crashes during the snapshot phase, the first change is rolled back, preventing corrupted partial states.

12. **Why did you use an `ArchiveSnapshot` table instead of just setting previous applications back to "Applied" during an undo?**
    *Answer*: Because applications were in different states before the offer was accepted—some were "Screening", some were "Interview", and some were "Saved". The Snapshot table records the exact state of *each* application so the rollback restores the timeline perfectly rather than blindly guessing a default state.

13. **What is idempotency and how did you handle it in the Accept Offer flow?**
    *Answer*: Idempotency means multiple identical requests have the same effect as a single request. I handled it by checking if an offer is already accepted before starting the transaction. This prevents issues if the user double-clicks the Accept button or submits the form twice due to network lag.
