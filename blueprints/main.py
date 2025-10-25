"""
Main blueprint for dashboard and home routes
"""
from flask import Blueprint, render_template, session

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def dashboard():
    """Main dashboard page"""
    # Get recent analyses from session
    recent_analyses = session.get('recent_analyses', [])
    return render_template('dashboard.html', recent_analyses=recent_analyses)