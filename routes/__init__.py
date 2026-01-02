# Routes Package
# Flask Blueprint routes for the application

from routes.generate import generate_bp
from routes.history import history_bp
from routes.prompt import prompt_bp
from routes.export import export_bp
from routes.templates import templates_bp
from routes.favorites import favorites_bp
from routes.llm import llm_bp


def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(generate_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(prompt_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(templates_bp)
    app.register_blueprint(favorites_bp)
    app.register_blueprint(llm_bp)
