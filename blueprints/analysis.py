"""
Analysis Blueprint - Stock analysis, comparison, and screening routes
"""
from flask import Blueprint, render_template, request, flash, session
from services.stock_service import stock_service
from utils.converters import safe_float, safe_int
from datetime import datetime

analysis_bp = Blueprint('analysis', __name__)

def add_to_recent_analyses(ticker, company_name, sector, price, eight_pillars_score):
    """Add analysis to recent analyses in session"""
    if 'recent_analyses' not in session:
        session['recent_analyses'] = []
    
    # Create analysis entry
    analysis_entry = {
        'ticker': ticker,
        'company_name': company_name,
        'sector': sector,
        'price': price,
        'eight_pillars_score': eight_pillars_score,
        'timestamp': datetime.now().isoformat()
    }
    
    # Add to beginning of list
    recent_analyses = session['recent_analyses']
    
    # Remove if already exists (to avoid duplicates)
    recent_analyses = [a for a in recent_analyses if a['ticker'] != ticker]
    
    # Add new entry at the beginning
    recent_analyses.insert(0, analysis_entry)
    
    # Keep only the last 5 analyses
    session['recent_analyses'] = recent_analyses[:5]
    session.modified = True

@analysis_bp.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if request.method == 'POST':
        ticker = request.form.get('ticker', '').upper()
        discount_rate = safe_float(request.form.get('discount_rate', 0.125))
        
        if not ticker:
            flash('Please enter a stock symbol', 'error')
            return render_template('analyze.html')
        
        try:
            # Use stock service to get comprehensive analysis data
            analysis_data = stock_service.get_stock_analysis(ticker, discount_rate)
            
            if analysis_data.get('success'):
                # Store in recent analyses
                company_info = analysis_data.get('company_info', {})
                if hasattr(company_info, 'to_dict'):
                    company_info = company_info.to_dict()
                
                add_to_recent_analyses(
                    ticker=analysis_data.get('ticker'),
                    company_name=company_info.get('longName', ticker),
                    sector=company_info.get('sector', 'Technology'),
                    price=company_info.get('currentPrice', 0),
                    eight_pillars_score=analysis_data.get('eight_pillars_score', 0)
                )
                
                # Debug: Print what we're about to pass to template
                print(f"DEBUG: Passing analysis_data keys: {list(analysis_data.keys())}")
                print(f"DEBUG: Success flag: {analysis_data.get('success')}")
                print(f"DEBUG: Ticker: {analysis_data.get('ticker')}")
                
                # Convert pandas Series to dict if needed
                if 'company_info' in analysis_data and hasattr(analysis_data['company_info'], 'to_dict'):
                    analysis_data['company_info'] = analysis_data['company_info'].to_dict()
                    print("DEBUG: Converted company_info to dict")
                
                # Try rendering with explicit variables first
                print("DEBUG: Attempting to render template with explicit variables")
                try:
                    return render_template('analyze.html', 
                                         ticker=analysis_data.get('ticker'),
                                         success=analysis_data.get('success'),
                                         company_info=analysis_data.get('company_info'),
                                         chart_html=analysis_data.get('chart_html'),
                                         eight_pillars_html=analysis_data.get('eight_pillars_html'),
                                         eight_pillars_score=analysis_data.get('eight_pillars_score'),
                                         intrinsic_value_html=analysis_data.get('intrinsic_value_html'),
                                         valuation_recommendation=analysis_data.get('valuation_recommendation'),
                                         financial_statements=analysis_data.get('financial_statements'),
                                         financial_ratios=analysis_data.get('financial_ratios'),
                                         discount_rate=discount_rate)
                except Exception as e:
                    print(f"DEBUG: Template rendering failed: {e}")
                    return render_template('analyze.html', **analysis_data)
            else:
                flash(f'Error analyzing {ticker}: {analysis_data.get("error", "Unknown error")}', 'error')
                return render_template('analyze.html')
                                 
        except Exception as e:
            flash(f'Error analyzing {ticker}: {str(e)}', 'error')
            return render_template('analyze.html')
    
    else:
        # Handle GET request with ticker parameter (from screener "Analyze" buttons)
        ticker = request.args.get('ticker', '').upper()
        if ticker:
            discount_rate = safe_float(request.args.get('discount_rate', 0.125))
            
            try:
                # Use stock service to get comprehensive analysis data
                analysis_data = stock_service.get_stock_analysis(ticker, discount_rate)
                
                if analysis_data.get('success'):
                    # Store in recent analyses
                    company_info = analysis_data.get('company_info', {})
                    if hasattr(company_info, 'to_dict'):
                        company_info = company_info.to_dict()
                    
                    add_to_recent_analyses(
                        ticker=analysis_data.get('ticker'),
                        company_name=company_info.get('longName', ticker),
                        sector=company_info.get('sector', 'Technology'),
                        price=company_info.get('currentPrice', 0),
                        eight_pillars_score=analysis_data.get('eight_pillars_score', 0)
                    )
                    
                    # Debug: Print what we're about to pass to template
                    print(f"DEBUG: Passing analysis_data keys: {list(analysis_data.keys())}")
                    print(f"DEBUG: Success flag: {analysis_data.get('success')}")
                    print(f"DEBUG: Ticker: {analysis_data.get('ticker')}")
                    
                    # Convert pandas Series to dict if needed
                    if 'company_info' in analysis_data and hasattr(analysis_data['company_info'], 'to_dict'):
                        analysis_data['company_info'] = analysis_data['company_info'].to_dict()
                        print("DEBUG: Converted company_info to dict")
                    
                    # Try rendering with explicit variables first
                    print("DEBUG: Attempting to render template with explicit variables")
                    try:
                        return render_template('analyze.html', 
                                             ticker=analysis_data.get('ticker'),
                                             success=analysis_data.get('success'),
                                             company_info=analysis_data.get('company_info'),
                                             chart_html=analysis_data.get('chart_html'),
                                             eight_pillars_html=analysis_data.get('eight_pillars_html'),
                                             eight_pillars_score=analysis_data.get('eight_pillars_score'),
                                             intrinsic_value_html=analysis_data.get('intrinsic_value_html'),
                                             valuation_recommendation=analysis_data.get('valuation_recommendation'),
                                             financial_statements=analysis_data.get('financial_statements'),
                                             financial_ratios=analysis_data.get('financial_ratios'),
                                             discount_rate=discount_rate)
                    except Exception as e:
                        print(f"DEBUG: Template rendering failed: {e}")
                        return render_template('analyze.html', **analysis_data)
                else:
                    flash(f'Error analyzing {ticker}: {analysis_data.get("error", "Unknown error")}', 'error')
                    return render_template('analyze.html')
                                     
            except Exception as e:
                flash(f'Error analyzing {ticker}: {str(e)}', 'error')
                return render_template('analyze.html')
    
    return render_template('analyze.html')

@analysis_bp.route('/compare', methods=['GET', 'POST'])
def compare():
    if request.method == 'POST':
        # Handle POST request from form submission
        tickers_input = request.form.get('tickers', '').upper()
        symbols = [s.strip() for s in tickers_input.split(',') if s.strip()]
        
        if len(symbols) < 2:
            flash('Please enter at least 2 stock symbols separated by commas', 'error')
            return render_template('compare.html')
        
        try:
            # Use stock service to compare stocks
            comparison_data = stock_service.compare_stocks(symbols)
            
            return render_template('compare.html', **comparison_data)
                                 
        except Exception as e:
            flash(f'Error comparing stocks: {str(e)}', 'error')
            return render_template('compare.html')
    
    else:
        # Handle GET request with tickers parameter (from screener "Compare All Results" button)
        tickers_param = request.args.get('tickers', '')
        if tickers_param:
            symbols = [s.strip().upper() for s in tickers_param.split(',') if s.strip()]
            
            if len(symbols) < 2:
                flash('Please select at least 2 stocks to compare', 'error')
                return render_template('compare.html')
            
            try:
                # Use stock service to compare stocks
                comparison_data = stock_service.compare_stocks(symbols)
                
                return render_template('compare.html', **comparison_data)
                                     
            except Exception as e:
                flash(f'Error comparing stocks: {str(e)}', 'error')
                return render_template('compare.html')
    
    return render_template('compare.html')

@analysis_bp.route('/screener', methods=['GET', 'POST'])
def screener():
    if request.method == 'POST':
        # Get screening criteria from form and map to stock service parameters
        criteria = {
            'market_cap_min': safe_float(request.form.get('market_cap_min')),
            'market_cap_max': safe_float(request.form.get('market_cap_max')),
            'pe_ratio_max': safe_float(request.form.get('pe_ratio_max')),
            'price_book_max': safe_float(request.form.get('price_book_max')),
            'debt_to_equity_max': safe_float(request.form.get('debt_equity_max')),
            'roe_min': safe_float(request.form.get('roe_min')),
            'sector': request.form.get('sector') if request.form.get('sector') else None,
            'min_pillars_score': safe_float(request.form.get('min_pillars_score'))
        }
        
        try:
            # Use stock service to screen stocks
            screener_data = stock_service.screen_stocks(criteria)
            
            if screener_data.get('success'):
                results = screener_data.get('results', [])
                # Pass the results to template with proper variable name
                return render_template('screener.html', 
                                     screening_results=results,
                                     criteria=criteria,
                                     success=True)
            else:
                flash(f'Error screening stocks: {screener_data.get("error", "Unknown error")}', 'error')
                return render_template('screener.html', criteria=criteria)
                                 
        except Exception as e:
            flash(f'Error screening stocks: {str(e)}', 'error')
            return render_template('screener.html', criteria=criteria)
    
    return render_template('screener.html', criteria={})