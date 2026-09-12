from app import create_app
from models import db, Company, Application, Interaction, StatusHistory
from datetime import datetime, date, timedelta, timezone
import random

def seed_data():
    app = create_app()
    with app.app_context():
        # Clear existing data (optional, useful for clean start)
        db.drop_all()
        db.create_all()

        print("Seeding database...")

        # 1. Create Companies
        companies_data = [
            {"name": "Google", "website": "https://careers.google.com", "industry": "Technology"},
            {"name": "Microsoft", "website": "https://careers.microsoft.com", "industry": "Technology"},
            {"name": "Stripe", "website": "https://stripe.com/jobs", "industry": "FinTech"},
            {"name": "Airbnb", "website": "https://careers.airbnb.com", "industry": "Travel Tech"},
            {"name": "Netflix", "website": "https://jobs.netflix.com", "industry": "Entertainment"},
            {"name": "Spotify", "website": "https://lifeatspotify.com", "industry": "Audio Streaming"},
            {"name": "Datadog", "website": "https://careers.datadoghq.com", "industry": "Cloud Monitoring"},
            {"name": "Vercel", "website": "https://vercel.com/careers", "industry": "Web Development"},
        ]

        companies = []
        for c_data in companies_data:
            company = Company(**c_data)
            db.session.add(company)
            companies.append(company)
            
        db.session.commit()

        # 2. Create Applications
        job_titles = ["Software Engineer", "Backend Developer", "Full Stack Engineer", "Python Developer", "Data Engineer"]
        locations = ["Remote", "New York, NY", "San Francisco, CA", "Seattle, WA", "Austin, TX"]
        statuses = ["Saved", "Applied", "Screening", "Interview", "Offer", "Rejected", "Accepted"]
        priorities = ["Low", "Medium", "High"]

        applications = []
        for i in range(15):
            company = random.choice(companies)
            status = random.choice(statuses)
            
            # Create a logical timeline
            days_ago = random.randint(5, 60)
            applied_date = date.today() - timedelta(days=days_ago) if status != "Saved" else None
            
            # Follow up if active
            follow_up = None
            if status in ["Applied", "Screening", "Interview"]:
                follow_up = date.today() + timedelta(days=random.randint(-2, 5))
                
            created = datetime.now(timezone.utc) - timedelta(days=days_ago + 2)
            updated = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 10))

            app_obj = Application(
                company_id=company.id,
                job_title=random.choice(job_titles),
                job_url=f"{company.website}/job/{random.randint(1000, 9999)}",
                salary_range=f"${random.randint(100, 150)}k - ${random.randint(150, 200)}k",
                location=random.choice(locations),
                status=status,
                applied_date=applied_date,
                follow_up_date=follow_up,
                priority=random.choice(priorities),
                created_at=created,
                updated_at=updated
            )
            db.session.add(app_obj)
            applications.append(app_obj)
            
        db.session.commit()

        # 3. Create Interactions and History
        interaction_types = ["Email", "Call", "Interview", "Assessment"]
        
        for app_obj in applications:
            # Manually seed status history to match current status
            if app_obj.status != "Saved":
                hist1 = StatusHistory(
                    application_id=app_obj.id,
                    old_status="Saved",
                    new_status="Applied",
                    changed_at=app_obj.created_at + timedelta(days=1)
                )
                db.session.add(hist1)
                
                if app_obj.status in ["Screening", "Interview", "Offer", "Rejected", "Accepted"]:
                    hist2 = StatusHistory(
                        application_id=app_obj.id,
                        old_status="Applied",
                        new_status=app_obj.status,
                        changed_at=app_obj.updated_at
                    )
                    db.session.add(hist2)
            
            # Seed 0-3 interactions per app
            num_interactions = random.randint(0, 3)
            for _ in range(num_interactions):
                interaction_date = app_obj.created_at + timedelta(days=random.randint(1, 10))
                interaction = Interaction(
                    application_id=app_obj.id,
                    type=random.choice(interaction_types),
                    date=interaction_date,
                    notes=f"Discussed the role requirements and next steps. Went well." if random.random() > 0.5 else "Sent follow-up email to recruiter."
                )
                db.session.add(interaction)
                
        db.session.commit()
        print("Database seeded successfully with 15 dummy applications!")

if __name__ == "__main__":
    seed_data()
