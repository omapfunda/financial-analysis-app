"""
API Blueprint - API endpoints for AJAX requests
"""
from flask import Blueprint, jsonify, request
from services.stock_service import stock_service
from services.portfolio_service import portfolio_service
from services.analytics_service import analytics_service
from utils.converters import safe_float

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/screen', methods=['GET', 'POST'])
def api_screen():
    """API endpoint for stock screening"""
    try:
        # Get screening criteria from request
        criteria = {}
        if request.json:
            criteria = request.json
        else:
            criteria = {
                'market_cap_min': safe_float(request.form.get('min_market_cap')),
                'market_cap_max': safe_float(request.form.get('max_market_cap')),
                'pe_ratio_max': safe_float(request.form.get('max_pe_ratio')),
                'price_book_max': safe_float(request.form.get('price_book_max')),
                'debt_to_equity_max': safe_float(request.form.get('debt_equity_max')),
                'roe_min': safe_float(request.form.get('roe_min')),
                'sector': request.form.get('sector') if request.form.get('sector') else None,
                'min_pillars_score': safe_float(request.form.get('min_pillars_score'))
            }
        
        # Use stock service to screen stocks
        results = stock_service.screen_stocks(criteria)
        
        return jsonify({
            'success': True,
            'results': results.get('results', []),
            'count': len(results.get('results', []))
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/portfolio/<int:portfolio_id>/value')
def api_portfolio_value(portfolio_id):
    """API endpoint for portfolio value"""
    try:
        portfolio_value = portfolio_service.get_portfolio_value(portfolio_id)
        if portfolio_value:
            return jsonify({
                'success': True,
                'data': portfolio_value
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Portfolio not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/stock/<symbol>/price')
def api_stock_price(symbol):
    """API endpoint for current stock price"""
    try:
        price = stock_service.get_stock_price(symbol.upper())
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'price': price
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/portfolio/<int:portfolio_id>/analytics')
def api_portfolio_analytics(portfolio_id):
    """API endpoint for portfolio analytics"""
    try:
        analytics_data = analytics_service.get_portfolio_analytics(portfolio_id)
        return jsonify({
            'success': True,
            'data': analytics_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/portfolio/<int:portfolio_id>/performance')
def api_portfolio_performance(portfolio_id):
    """API endpoint for portfolio performance metrics"""
    try:
        performance = analytics_service.calculate_portfolio_performance(portfolio_id)
        return jsonify({'success': True, 'data': performance})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/portfolio/<int:portfolio_id>/risk')
def api_portfolio_risk(portfolio_id):
    """API endpoint for portfolio risk metrics"""
    try:
        risk_metrics = analytics_service.calculate_risk_metrics(portfolio_id)
        return jsonify({'success': True, 'data': risk_metrics})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/portfolio/<int:portfolio_id>/sector_allocation')
def api_portfolio_sector_allocation(portfolio_id):
    """API endpoint for portfolio sector allocation"""
    try:
        sector_allocation = analytics_service.get_sector_allocation(portfolio_id)
        return jsonify({'success': True, 'data': sector_allocation})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/portfolio/<int:portfolio_id>/correlation_matrix')
def api_portfolio_correlation_matrix(portfolio_id):
    """API endpoint for portfolio correlation matrix"""
    try:
        correlation_matrix = analytics_service.get_correlation_matrix(portfolio_id)
        return jsonify({'success': True, 'data': correlation_matrix})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/portfolio/<int:portfolio_id>/optimize')
def api_portfolio_optimize(portfolio_id):
    """API endpoint for portfolio optimization"""
    try:
        optimization_results = analytics_service.optimize_portfolio(portfolio_id)
        return jsonify({'success': True, 'data': optimization_results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/portfolio/<int:portfolio_id>/rebalance')
def api_portfolio_rebalance(portfolio_id):
    """API endpoint for portfolio rebalancing recommendations"""
    try:
        strategy = request.args.get('strategy', 'max_sharpe')
        rebalancing = analytics_service.get_rebalancing_recommendations(portfolio_id, strategy)
        return jsonify({'success': True, 'data': rebalancing})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/portfolio/<int:portfolio_id>/efficiency')
def api_portfolio_efficiency(portfolio_id):
    """API endpoint for portfolio efficiency analysis"""
    try:
        efficiency_analysis = analytics_service.analyze_efficiency(portfolio_id)
        return jsonify({'success': True, 'data': efficiency_analysis})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500