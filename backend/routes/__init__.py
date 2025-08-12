from .api import bp as api_bp
from .admin import bp as admin_bp
from .root import bp as root_bp
from .auth import bp as auth_bp, login_manager
from .groups import bp as groups_bp
from .predictions import bp as preds_bp
from .leaderboard import bp as leaderboard_bp

def register_blueprints(app):
    app.register_blueprint(root_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(preds_bp)
    app.register_blueprint(leaderboard_bp)
    login_manager.init_app(app)