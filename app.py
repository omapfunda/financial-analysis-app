#!/usr/bin/env python3
"""
Financial Analysis Web Application
A comprehensive Flask application for stock analysis, portfolio management, and financial screening.
"""
import os
from flask import Flask, jsonify, render_template, session
from blueprints.main import main_bp
from blueprints.analysis import analysis_bp
from blueprints.portfolio import portfolio_bp
from blueprints.api import api_bp
from config.config import get_config
from utils.error_handler import app_logger, ErrorHandler

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    config_obj = get_config()
    app.config.from_object(config_obj)
    
    # Set secret key for sessions (use environment variable in production)
    app.secret_key = os.environ.get('SECRET_KEY', 'financial_analysis_secret_key_2025')
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(api_bp)
    
    # Simple error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        if '/api/' in str(error):
            return jsonify({
                'success': False,
                'error': {
                    'type': 'not_found',
                    'message': 'API endpoint not found'
                }
            }), 404
        return render_template('error.html', 
                             error_code=404, 
                             error_message="Page not found"), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        if '/api/' in str(error):
            return jsonify({
                'success': False,
                'error': {
                    'type': 'internal_error',
                    'message': 'Internal server error'
                }
            }), 500
        return render_template('error.html', 
                             error_code=500, 
                             error_message="Internal server error"), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("Starting Flask application...")
    
    # Use environment variables for host and port (for deployment)
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    app.run(host=host, port=port, debug=debug)