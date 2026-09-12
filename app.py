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
        db.create_all()
        
    return app

if __name__ == '__main__':
    # Run the application
    app = create_app()
    app.run(debug=True)
