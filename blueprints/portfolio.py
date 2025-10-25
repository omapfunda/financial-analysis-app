"""Portfolio Blueprint - Portfolio management routes"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from services.portfolio_service import portfolio_service
from utils.converters import safe_float

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/portfolio')
def portfolio():
    """Portfolio overview page"""
    result = portfolio_service.get_all_portfolios()
    if result['success']:
        portfolios = result['portfolios']
    else:
        portfolios = []
        flash(f'Error loading portfolios: {result.get("error", "Unknown error")}', 'error')
    return render_template('portfolio.html', portfolios=portfolios)

@portfolio_bp.route('/portfolio/create', methods=['GET', 'POST'])
def create_portfolio():
    """Create new portfolio"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if not name:
            flash('Portfolio name is required', 'error')
            return render_template('create_portfolio.html')
        
        try:
            portfolio_id = portfolio_service.create_portfolio(name, description)
            flash(f'Portfolio "{name}" created successfully', 'success')
            return redirect(url_for('portfolio.view_portfolio', portfolio_id=portfolio_id))
        except Exception as e:
            flash(f'Error creating portfolio: {str(e)}', 'error')
    
    return render_template('create_portfolio.html')

@portfolio_bp.route('/portfolio/<int:portfolio_id>')
def view_portfolio(portfolio_id):
    """View specific portfolio"""
    try:
        portfolio_data = portfolio_service.get_portfolio_details(portfolio_id)
        if not portfolio_data:
            flash('Portfolio not found', 'error')
            return redirect(url_for('portfolio.portfolio'))
        
        return render_template('view_portfolio.html', **portfolio_data)
    except Exception as e:
        flash(f'Error loading portfolio: {str(e)}', 'error')
        return redirect(url_for('portfolio.portfolio'))

@portfolio_bp.route('/portfolio/<int:portfolio_id>/add_stock', methods=['POST'])
def add_stock(portfolio_id):
    """Add stock to portfolio"""
    symbol = request.form.get('symbol', '').upper()
    shares = safe_float(request.form.get('shares'))
    purchase_price = safe_float(request.form.get('purchase_price'))
    
    if not symbol or not shares or not purchase_price:
        flash('All fields are required', 'error')
        return redirect(url_for('portfolio.view_portfolio', portfolio_id=portfolio_id))
    
    try:
        portfolio_service.add_stock_to_portfolio(portfolio_id, symbol, shares, purchase_price)
        flash(f'Added {shares} shares of {symbol} to portfolio', 'success')
    except Exception as e:
        flash(f'Error adding stock: {str(e)}', 'error')
    
    return redirect(url_for('portfolio.view_portfolio', portfolio_id=portfolio_id))

@portfolio_bp.route('/portfolio/<int:portfolio_id>/remove_stock', methods=['POST'])
def remove_stock_from_portfolio(portfolio_id):
    """Remove/sell stock from portfolio"""
    symbol = request.form.get('symbol', '').upper()
    shares = safe_float(request.form.get('shares'))
    
    if not symbol:
        flash('Please provide a valid symbol', 'error')
        return redirect(url_for('portfolio.view_portfolio', portfolio_id=portfolio_id))
    
    try:
        portfolio_service.remove_stock_from_portfolio(portfolio_id, symbol, shares)
        action = f"Sold {shares} shares of {symbol}" if shares else f"Sold all shares of {symbol}"
        flash(action, 'success')
    except Exception as e:
        flash(f'Error removing stock: {str(e)}', 'error')
    
    return redirect(url_for('portfolio.view_portfolio', portfolio_id=portfolio_id))

@portfolio_bp.route('/portfolio/<int:portfolio_id>/edit', methods=['GET', 'POST'])
def edit_portfolio(portfolio_id):
    """Edit portfolio metadata"""
    try:
        portfolio = portfolio_service.get_portfolio(portfolio_id)
        if not portfolio:
            flash('Portfolio not found', 'error')
            return redirect(url_for('portfolio.portfolio'))
        
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            
            if not name:
                flash('Portfolio name is required', 'error')
                return render_template('edit_portfolio.html', portfolio=portfolio)
            
            portfolio_service.update_portfolio(portfolio_id, name, description)
            flash('Portfolio updated successfully!', 'success')
            return redirect(url_for('portfolio.view_portfolio', portfolio_id=portfolio_id))
        
        return render_template('edit_portfolio.html', portfolio=portfolio)
    except Exception as e:
        flash(f'Error editing portfolio: {str(e)}', 'error')
        return redirect(url_for('portfolio.portfolio'))

@portfolio_bp.route('/portfolio/<int:portfolio_id>/delete', methods=['POST'])
def delete_portfolio(portfolio_id):
    """Delete a portfolio"""
    try:
        portfolio_service.delete_portfolio(portfolio_id)
        flash('Portfolio deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting portfolio: {str(e)}', 'error')
    
    return redirect(url_for('portfolio.portfolio'))

# Portfolio Analytics Routes
@portfolio_bp.route('/portfolio/<int:portfolio_id>/analytics')
def portfolio_analytics(portfolio_id):
    """Portfolio analytics dashboard"""
    try:
        analytics_data = portfolio_service.get_portfolio_analytics(portfolio_id)
        if not analytics_data:
            flash('Portfolio not found', 'error')
            return redirect(url_for('portfolio.portfolio'))
        
        return render_template('portfolio_analytics.html', **analytics_data)
    except Exception as e:
        flash(f'Error calculating analytics: {str(e)}', 'error')
        return redirect(url_for('portfolio.view_portfolio', portfolio_id=portfolio_id))

# Portfolio Optimization Routes
@portfolio_bp.route('/portfolio/<int:portfolio_id>/optimize')
def portfolio_optimize(portfolio_id):
    """Portfolio optimization dashboard"""
    try:
        optimization_data = portfolio_service.get_portfolio_optimization(portfolio_id)
        if not optimization_data:
            flash('Portfolio not found', 'error')
            return redirect(url_for('portfolio.portfolio'))
        
        return render_template('portfolio_optimize.html', **optimization_data)
    except Exception as e:
        flash(f'Error during optimization: {str(e)}', 'error')
        return redirect(url_for('portfolio.view_portfolio', portfolio_id=portfolio_id))