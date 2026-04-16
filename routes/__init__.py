# Routes Package
# Flask Blueprint routes for the application

from routes.generate import generate_bp
from routes.history import history_bp
from routes.prompt import prompt_bp
from routes.export import export_bp
from routes.templates import templates_bp
from routes.favorites import favorites_bp
from routes.llm import llm_bp
from routes.models import models_bp
from routes.img2img import img2img_bp
from routes.gallery import gallery_bp
from routes.api import api_bp
from routes.dashboard import dashboard_bp
from routes.projects import projects_bp
from routes.queue import queue_bp
from routes.prompt_library import prompt_library_bp
from routes.story import story_bp


def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(generate_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(prompt_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(templates_bp)
    app.register_blueprint(favorites_bp)
    app.register_blueprint(llm_bp)
    app.register_blueprint(models_bp)
    app.register_blueprint(img2img_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(queue_bp)
    app.register_blueprint(prompt_library_bp)
    app.register_blueprint(story_bp)
