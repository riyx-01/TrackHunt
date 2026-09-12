from models import db, Application, Company, Interaction, StatusHistory, ArchiveSnapshot
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import func
import csv
from io import StringIO

def get_dashboard_stats():
    """
    Calculates statistics for the dashboard cards.
    Keeps complex queries out of the routes file.
    """
    total_apps = Application.query.filter(Application.status != 'Archived').count()
    
    # Calculate interviews this month
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # We query interactions where type is Interview and date is in the current month/year
    # extract('month', date) works in most databases including SQLite and PostgreSQL
    interviews_this_month = Interaction.query.filter(
        Interaction.type == 'Interview',
        db.extract('month', Interaction.date) == current_month,
        db.extract('year', Interaction.date) == current_year
    ).count()
    
    # Response rate: Apps that moved past 'Applied' or 'Saved'
    responded_apps = Application.query.filter(
        Application.status.notin_(['Saved', 'Applied', 'Archived'])
    ).count()
    
    # Avoid division by zero
    total_applied_or_more = Application.query.filter(
        Application.status.notin_(['Saved', 'Archived'])
    ).count()
    
    response_rate = 0
    if total_applied_or_more > 0:
        response_rate = round((responded_apps / total_applied_or_more) * 100)
        
    return {
        'total_apps': total_apps,
        'interviews_this_month': interviews_this_month,
        'response_rate': response_rate,
        # A true avg days to first response requires complex timestamp diffing.
        # For simplicity, we'll return a placeholder or calculate based on python date diffs.
        'avg_days_to_response': calculate_avg_days_to_response()
    }

def calculate_avg_days_to_response():
    """Helper function to calculate average days from Applied to Screening/Interview"""
    # Find all status history records where status changed FROM Applied TO Screening/Interview
    # This requires a more complex query, so for now we'll do it in memory for the sake of simplicity.
    # In a real large-scale app, you'd do this in SQL.
    
    applications = Application.query.all()
    total_days = 0
    count = 0
    
    for app in applications:
        if app.status in ['Saved', 'Applied']:
            continue
            
        applied_hist = next((h for h in app.status_history if h.new_status == 'Applied'), None)
        responded_hist = next((h for h in app.status_history if h.new_status in ['Screening', 'Interview', 'Rejected']), None)
        
        # If we have both, calculate the difference
        if applied_hist and responded_hist:
            diff = (responded_hist.changed_at - applied_hist.changed_at).days
            if diff >= 0:
                total_days += diff
                count += 1
                
    if count == 0:
        return "N/A"
    return f"{round(total_days / count)} days"

def get_needs_attention():
    """
    Returns applications that need attention:
    1. follow_up_date is today or in the past
    2. OR updated_at is more than 7 days ago AND status is not Rejected/Accepted
    """
    today = date.today()
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    
    # We use OR (|) operator in SQLAlchemy
    attention_apps = Application.query.filter(
        (Application.follow_up_date <= today) |
        ((Application.updated_at < seven_days_ago) & (~Application.status.in_(['Rejected', 'Accepted', 'Archived'])))
    ).all()
    
    return attention_apps

def get_chart_data():
    """
    Generates data for the Chart.js applications per week chart (last 12 weeks).
    """
    # To keep it simple for SQLite without complex date-math SQL functions:
    # We'll pull recent applications and group them in Python.
    twelve_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=12)
    recent_apps = Application.query.filter(
        Application.created_at >= twelve_weeks_ago,
        Application.status != 'Archived'
    ).all()
    
    # Initialize a dictionary for the last 12 weeks
    weeks_data = {}
    
    # Create the labels and zero-filled data first
    for i in range(11, -1, -1):
        start_of_week = (date.today() - timedelta(days=date.today().weekday()) - timedelta(weeks=i))
        label = start_of_week.strftime('%b %d')
        weeks_data[label] = 0
        
    # Populate with actual data
    for app in recent_apps:
        # Get start of week for the app's creation date
        app_date = app.created_at.date()
        start_of_week = app_date - timedelta(days=app_date.weekday())
        label = start_of_week.strftime('%b %d')
        if label in weeks_data:
            weeks_data[label] += 1
            
    return {
        'labels': list(weeks_data.keys()),
        'data': list(weeks_data.values())
    }

def generate_csv_export():
    """
    Generates a CSV string containing all applications.
    """
    applications = Application.query.join(Company).all()
    
    # Use StringIO to write CSV data to a string buffer
    si = StringIO()
    cw = csv.writer(si)
    
    # Header row
    cw.writerow([
        'Company', 'Job Title', 'Status', 'Location', 'Salary', 
        'Applied Date', 'Priority', 'Job URL'
    ])
    
    # Data rows
    for app in applications:
        cw.writerow([
            app.company.name,
            app.job_title,
            app.status,
            app.location or '',
            app.salary_range or '',
            app.applied_date.strftime('%Y-%m-%d') if app.applied_date else '',
            app.priority,
            app.job_url or ''
        ])
        
    return si.getvalue()

def get_current_accepted_offer():
    """Returns the currently accepted application, if any."""
    return Application.query.filter_by(status='Accepted').first()

def accept_offer_transaction(application_id):
    """
    Atomic transaction to accept an offer and archive all other active applications.
    Uses db.session to ensure either everything succeeds or everything fails (Atomicity).
    """
    # 1. Idempotency Check: if there's already an accepted offer, abort.
    if get_current_accepted_offer():
        raise ValueError("An offer is already accepted. Undo the previous acceptance first.")
        
    target_app = Application.query.get(application_id)
    if not target_app:
        raise ValueError("Application not found.")
        
    try:
        # Fetch all other non-terminal applications
        other_apps = Application.query.filter(
            Application.id != application_id,
            Application.status.notin_(['Rejected', 'Accepted', 'Archived'])
        ).all()
        
        # Snapshot and Archive others
        for app in other_apps:
            snapshot = ArchiveSnapshot(
                application_id=app.id,
                previous_status=app.status,
                accept_event_id=target_app.id
            )
            db.session.add(snapshot)
            app.status = 'Archived'
            
        # Snapshot the accepted one as well so we can restore its exact state (e.g. 'Offer')
        target_snapshot = ArchiveSnapshot(
            application_id=target_app.id,
            previous_status=target_app.status,
            accept_event_id=target_app.id
        )
        db.session.add(target_snapshot)
        
        # Set target to Accepted and ensure banner is not dismissed
        target_app.status = 'Accepted'
        target_app.is_accepted_banner_dismissed = False
        
        # Commit the transaction. If anything fails here, an exception is thrown.
        db.session.commit()
    except Exception as e:
        # Rollback the transaction on failure (Atomicity)
        db.session.rollback()
        raise e

def rollback_acceptance(accept_event_id):
    """
    Restores applications to their state before the offer was accepted.
    """
    try:
        snapshots = ArchiveSnapshot.query.filter_by(accept_event_id=accept_event_id).all()
        
        for snapshot in snapshots:
            app = Application.query.get(snapshot.application_id)
            if app:
                # Only restore if it is still Archived (or Accepted for the target)
                # This prevents destroying manual user edits (e.g. if they manually moved an archived app to Rejected)
                if app.status in ['Archived', 'Accepted']:
                    app.status = snapshot.previous_status
                    
            # Delete the snapshot record
            db.session.delete(snapshot)
            
        # Commit changes
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e
