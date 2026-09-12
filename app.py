from flask import Flask, render_template
from models import db
from routes import bp

def create_app():
    """
    App Factory Pattern:
    Instead of creating the Flask app instance globally, we create it inside a function.
    This allows us to create multiple instances of our app (e.g., for testing) and
    helps avoid circular import issues with extensions like SQLAlchemy.
    """
    app = Flask(__name__)
    
    # Load configuration from our Config class
    app.config.from_object('config.Config')
    
    # Initialize SQLAlchemy with our app instance
    db.init_app(app)
    
    # Register blueprints (routes)
    # A blueprint is a way to organize a group of related views and other code.
    app.register_blueprint(bp)
    
    # Custom Error Handler for 404 Not Found
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
        
    # Ensure database tables are created before the first request
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()
        
        # Automatically seed default companies if they don't exist
        # This is especially helpful for new Vercel PostgreSQL deployments
        from models import Company
        default_companies = [
            {"name": "Google", "industry": "Technology"},
            {"name": "Microsoft", "industry": "Technology"},
            {"name": "Apple", "industry": "Technology"},
            {"name": "Meta", "industry": "Technology"},
            {"name": "Amazon", "industry": "Technology"},
            {"name": "Netflix", "industry": "Entertainment"},
            {"name": "Spotify", "industry": "Audio Streaming"},
            {"name": "Airbnb", "industry": "Travel Tech"},
            {"name": "Stripe", "industry": "FinTech"},
            {"name": "Vercel", "industry": "Web Development"},
            {"name": "OpenAI", "industry": "AI Research"}
        ]
        
        added_any = False
        for c_data in default_companies:
            if not Company.query.filter_by(name=c_data["name"]).first():
                db.session.add(Company(**c_data))
                added_any = True
                
        if added_any:
            db.session.commit()
            
    return app

# Vercel's serverless environment requires a globally scoped 'app' variable.
# We call our factory function here so the WSGI server can find it.
app = create_app()

if __name__ == '__main__':
    # Run the application locally
    app.run(debug=True)
