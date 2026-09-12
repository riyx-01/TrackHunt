from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, URL, Optional, Length

class CompanyForm(FlaskForm):
    """Form for adding or editing a company."""
    name = StringField('Company Name', validators=[DataRequired(), Length(max=100)])
    website = StringField('Website', validators=[Optional(), URL(), Length(max=255)])
    industry = StringField('Industry', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Company')

class ApplicationForm(FlaskForm):
    """Form for adding or editing a job application."""
    # We will populate the choices for company_id in the route, before rendering the form
    company_id = SelectField('Company', coerce=int, validators=[DataRequired()])
    
    job_title = StringField('Job Title', validators=[DataRequired(), Length(max=150)])
    job_url = StringField('Job Posting URL', validators=[Optional(), URL(), Length(max=500)])
    salary_range = StringField('Salary Range', validators=[Optional(), Length(max=100)])
    location = StringField('Location', validators=[Optional(), Length(max=150)])
    
    status = SelectField('Status', choices=[
        ('Saved', 'Saved'),
        ('Applied', 'Applied'),
        ('Screening', 'Screening'),
        ('Interview', 'Interview'),
        ('Offer', 'Offer'),
        ('Rejected', 'Rejected'),
        ('Accepted', 'Accepted'),
        ('Archived', 'Archived')
    ], validators=[DataRequired()])
    
    applied_date = DateField('Applied Date', validators=[Optional()])
    deadline = DateField('Application Deadline', validators=[Optional()])
    follow_up_date = DateField('Follow-up Date', validators=[Optional()])
    
    priority = SelectField('Priority', choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High')
    ], default='Medium', validators=[DataRequired()])
    
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Application')

class InteractionForm(FlaskForm):
    """Form for adding a new interaction log to an application."""
    type = SelectField('Type', choices=[
        ('Email', 'Email'),
        ('Call', 'Call'),
        ('Interview', 'Interview'),
        ('Assessment', 'Assessment'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Add Interaction')
