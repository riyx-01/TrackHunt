from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from sqlalchemy import event

# We instantiate SQLAlchemy here but DO NOT bind it to an app yet.
# It will be bound in app.py using db.init_app(app)
db = SQLAlchemy()

class Company(db.Model):
    """
    Represents a company the user is applying to.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    website = db.Column(db.String(255))
    industry = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    # Relationship to applications: One company can have many applications.
    # cascade="all, delete-orphan" means if we delete a company, its applications are deleted.
    applications = db.relationship('Application', backref='company', lazy=True, cascade="all, delete-orphan")

class Application(db.Model):
    """
    Represents a specific job application.
    """
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key linking this application to a specific company
    # Why FK? It enforces referential integrity (an application MUST belong to a valid company).
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    
    job_title = db.Column(db.String(150), nullable=False, index=True)
    job_url = db.Column(db.String(500))
    salary_range = db.Column(db.String(100))
    location = db.Column(db.String(150))
    
    # Status options: Saved, Applied, Screening, Interview, Offer, Rejected, Accepted
    status = db.Column(db.String(50), nullable=False, default='Saved', index=True)
    
    applied_date = db.Column(db.Date)
    deadline = db.Column(db.Date)
    follow_up_date = db.Column(db.Date, index=True)
    
    priority = db.Column(db.String(20), default='Medium') # Low, Medium, High
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Tracks if the user dismissed the celebration banner after accepting an offer
    is_accepted_banner_dismissed = db.Column(db.Boolean, default=False)

    # Relationships
    interactions = db.relationship('Interaction', backref='application', lazy=True, cascade="all, delete-orphan")
    status_history = db.relationship('StatusHistory', backref='application', lazy=True, cascade="all, delete-orphan")
    archive_snapshots = db.relationship('ArchiveSnapshot', backref='application', lazy=True, cascade="all, delete-orphan")

class Interaction(db.Model):
    """
    Logs a touchpoint (e.g., email, call) for an application.
    """
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False) # Email, Call, Interview
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    notes = db.Column(db.Text)

class StatusHistory(db.Model):
    """
    Automatically tracks changes to application status for velocity metrics.
    """
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False, index=True)
    old_status = db.Column(db.String(50))
    new_status = db.Column(db.String(50), nullable=False)
    changed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class ArchiveSnapshot(db.Model):
    """
    Stores a snapshot of an application's status right before it was archived.
    Enables safe rollback if the user undoes accepting an offer.
    """
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False, index=True)
    previous_status = db.Column(db.String(50), nullable=False)
    archived_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # Links this snapshot to the specific Application that was accepted
    accept_event_id = db.Column(db.Integer, nullable=False, index=True)

# SQLAlchemy Event Listener
# This function is triggered automatically right before an Application's 'status' field changes.
# It allows us to seamlessly log the change into the StatusHistory table without cluttering our routes.
@event.listens_for(Application.status, 'set')
def log_status_change(target, value, oldvalue, initiator):
    # Only log if the old value exists (meaning it's an update, not a new creation) 
    # and if the value is actually changing.
    # Note: When creating a new object, oldvalue is a special SQLAlchemy symbol, not a string.
    if oldvalue != value and hasattr(target, 'id') and target.id is not None and isinstance(oldvalue, str):
        history_entry = StatusHistory(
            application_id=target.id,
            old_status=oldvalue,
            new_status=value
        )
        # We use object_session(target) to get the current database session
        from sqlalchemy.orm.session import object_session
        session = object_session(target)
        if session:
            session.add(history_entry)
