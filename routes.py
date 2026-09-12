from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from models import db, Application, Company, Interaction
from forms import ApplicationForm, CompanyForm, InteractionForm
import services

# Create a blueprint named 'main'.
# Blueprints help organize routes. They are registered in app.py.
bp = Blueprint('main', __name__)

@bp.route('/')
def dashboard():
    """Renders the dashboard with stats, chart data, and 'needs attention' list."""
    stats = services.get_dashboard_stats()
    chart_data = services.get_chart_data()
    needs_attention = services.get_needs_attention()
    accepted_offer = services.get_current_accepted_offer()
    
    return render_template('dashboard.html', 
                           stats=stats, 
                           chart_data=chart_data, 
                           needs_attention=needs_attention,
                           accepted_offer=accepted_offer)

@bp.route('/applications')
def application_list():
    """List view with filtering and search."""
    # Get query parameters from the URL (e.g., /applications?status=Applied&q=Google)
    status_filter = request.args.get('status')
    q_filter = request.args.get('q')
    
    # Start with a base query joining Company so we can search by company name
    query = Application.query.join(Company)
    
    if status_filter:
        query = query.filter(Application.status == status_filter)
        
    if q_filter:
        # Search in company name OR job title
        search_term = f"%{q_filter}%"
        query = query.filter(
            (Company.name.ilike(search_term)) | 
            (Application.job_title.ilike(search_term))
        )
        
    # Order by most recently updated
    applications = query.order_by(Application.updated_at.desc()).all()
    
    accepted_offer = services.get_current_accepted_offer()
    
    return render_template('applications.html', applications=applications, accepted_offer=accepted_offer)

@bp.route('/applications/new', methods=['GET', 'POST'])
def new_application():
    """Create a new application."""
    form = ApplicationForm()
    
    # Populate the company choices for the dropdown. 
    # Must be done before validating the form.
    form.company_id.choices = [(c.id, c.name) for c in Company.query.order_by(Company.name).all()]
    
    if form.validate_on_submit():
        # Form is valid, create the Application object
        app = Application(
            company_id=form.company_id.data,
            job_title=form.job_title.data,
            job_url=form.job_url.data,
            salary_range=form.salary_range.data,
            location=form.location.data,
            status=form.status.data,
            applied_date=form.applied_date.data,
            deadline=form.deadline.data,
            follow_up_date=form.follow_up_date.data,
            priority=form.priority.data,
            notes=form.notes.data
        )
        db.session.add(app)
        db.session.commit()
        
        flash('Application saved successfully!', 'success')
        return redirect(url_for('main.application_detail', id=app.id))
        
    # Also provide a CompanyForm in case the user needs to add a new company directly from this page
    company_form = CompanyForm()
        
    return render_template('application_form.html', form=form, company_form=company_form, title="New Application")

@bp.route('/applications/<int:id>')
def application_detail(id):
    """View details and interaction history for a single application."""
    # get_or_404 will automatically return our custom 404 page if the ID doesn't exist
    application = Application.query.get_or_404(id)
    interaction_form = InteractionForm()
    return render_template('application_detail.html', application=application, interaction_form=interaction_form)

@bp.route('/applications/<int:id>/edit', methods=['GET', 'POST'])
def edit_application(id):
    """Edit an existing application."""
    application = Application.query.get_or_404(id)
    form = ApplicationForm(obj=application)
    form.company_id.choices = [(c.id, c.name) for c in Company.query.order_by(Company.name).all()]
    
    if form.validate_on_submit():
        # Update the object with the form data.
        # SQLAlchemy will automatically trigger our status_change event listener if the status changed.
        form.populate_obj(application)
        db.session.commit()
        
        flash('Application updated successfully!', 'success')
        return redirect(url_for('main.application_detail', id=application.id))
        
    return render_template('application_form.html', form=form, title="Edit Application", application=application)

@bp.route('/applications/<int:id>/delete', methods=['GET', 'POST'])
def delete_application(id):
    """
    Delete an application. 
    Never use a simple GET request for deletion to prevent accidental deletes 
    (e.g., from web crawlers or pre-fetching).
    """
    application = Application.query.get_or_404(id)
    
    if request.method == 'POST':
        db.session.delete(application)
        db.session.commit()
        flash(f'Application for {application.job_title} deleted.', 'success')
        return redirect(url_for('main.dashboard'))
        
    return render_template('confirm_delete.html', application=application)

@bp.route('/companies/new', methods=['POST'])
def new_company():
    """Endpoint specifically for the modal/inline form to add a company."""
    form = CompanyForm()
    if form.validate_on_submit():
        # Check for duplicates
        existing = Company.query.filter(Company.name.ilike(form.name.data)).first()
        if existing:
            flash(f"Company '{form.name.data}' already exists.", 'warning')
        else:
            company = Company(
                name=form.name.data,
                website=form.website.data,
                industry=form.industry.data,
                notes=form.notes.data
            )
            db.session.add(company)
            db.session.commit()
            flash(f"Company '{form.name.data}' added successfully.", 'success')
            
    # Redirect back to where they came from
    return redirect(request.referrer or url_for('main.dashboard'))

@bp.route('/applications/<int:id>/interactions', methods=['POST'])
def add_interaction(id):
    """Add a new interaction to an application."""
    application = Application.query.get_or_404(id)
    form = InteractionForm()
    
    if form.validate_on_submit():
        interaction = Interaction(
            application_id=application.id,
            type=form.type.data,
            date=form.date.data,
            notes=form.notes.data
        )
        db.session.add(interaction)
        
        # Adding an interaction means we touched the app, so update 'updated_at'
        application.updated_at = db.func.now()
        db.session.commit()
        
        flash('Interaction logged.', 'success')
        
    return redirect(url_for('main.application_detail', id=application.id))

@bp.route('/export')
def export_csv():
    """Download applications as CSV."""
    csv_data = services.generate_csv_export()
    
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=applications.csv"}
    )

@bp.route('/applications/<int:id>/accept', methods=['POST'])
def accept_offer(id):
    """Atomic endpoint to accept an offer and archive others."""
    try:
        services.accept_offer_transaction(id)
        flash('Congratulations on accepting the offer! 🎉 Other applications have been archived.', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        
    return redirect(url_for('main.dashboard'))

@bp.route('/applications/rollback/<int:event_id>', methods=['POST'])
def rollback_offer(event_id):
    """Rolls back an accepted offer and restores archived applications."""
    try:
        services.rollback_acceptance(event_id)
        flash('Offer acceptance undone. Applications restored to their previous states.', 'info')
    except Exception as e:
        flash(f'An error occurred during rollback: {str(e)}', 'danger')
        
    # Redirect to where the user came from, or dashboard as fallback
    return redirect(request.referrer or url_for('main.dashboard'))

@bp.route('/applications/<int:id>/dismiss_banner', methods=['POST'])
def dismiss_banner(id):
    """Dismisses the celebration banner for a specific accepted application."""
    app = Application.query.get_or_404(id)
    if app.status == 'Accepted':
        app.is_accepted_banner_dismissed = True
        db.session.commit()
    return redirect(url_for('main.dashboard'))
