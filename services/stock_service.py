"""Stock Service - Centralized business logic for stock operations"""
from macrotrends_api import Ticker, Tickers, real_stock_screener
from utils.converters import safe_float
from utils.scoring import calculate_eight_pillars_score, calculate_financial_strength_score
from utils.recommendations import get_valuation_recommendation, get_risk_recommendation
from utils.formatters import format_financial_dataframe, format_number, format_percentage
from utils.error_handler import handle_errors, log_function_call, ValidationError, ExternalAPIError
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import json
import logging

logger = logging.getLogger(__name__)


class StockService:
    """Service class for stock-related operations"""
    
    def __init__(self):
        self.cache = {}  # Simple in-memory cache
    
    @handle_errors(error_type='web')
    @log_function_call
    def analyze_stock(self, ticker):
        """Comprehensive stock analysis"""
        if not ticker or not ticker.strip():
            raise ValidationError("Ticker symbol is required")
        
        try:
            stock = Ticker(ticker.upper())
            logger.info(f"Analyzing stock: {ticker.upper()}")
            
            # Get financial data
            income_statement = stock.income_statement_annual
            balance_sheet = stock.balance_sheet_annual
            cash_flow = stock.cash_flow_annual
            ratios = stock.financial_ratios_annual
            
            # Get eight pillars analysis
            eight_pillars = stock.eight_pillars
            
            # Calculate scores
            eight_pillars_score = 0
            if not eight_pillars.empty:
                eight_pillars_score = calculate_eight_pillars_score(eight_pillars)
            
            # Get recommendations
            company_info = stock.info
            current_price = company_info.get('last_close') if not company_info.empty else None
            
            # Get intrinsic value (using default discount rate of 12.5%)
            intrinsic_value_df = stock.intrinsic_value()
            intrinsic_val = None
            if not intrinsic_value_df.empty and 'Intrinsic Value' in intrinsic_value_df.index:
                intrinsic_val = intrinsic_value_df.loc['Intrinsic Value', ticker.upper()]
            
            valuation_rec = get_valuation_recommendation(current_price, intrinsic_val)
            
            # Format data for display
            formatted_income = format_financial_dataframe(income_statement)
            formatted_balance = format_financial_dataframe(balance_sheet)
            formatted_cash_flow = format_financial_dataframe(cash_flow)
            formatted_ratios = format_financial_dataframe(ratios)
            formatted_pillars = format_financial_dataframe(eight_pillars)
            
            logger.info(f"Successfully analyzed stock: {ticker.upper()}")
            return {
                'ticker': ticker.upper(),
                'income_statement': formatted_income,
                'balance_sheet': formatted_balance,
                'cash_flow': formatted_cash_flow,
                'ratios': formatted_ratios,
                'eight_pillars': formatted_pillars,
                'eight_pillars_score': eight_pillars_score,
                'valuation_recommendation': valuation_rec
            }
        except Exception as e:
            logger.error(f"Failed to analyze stock {ticker}: {str(e)}")
            raise ExternalAPIError(f"Failed to retrieve data for {ticker}: {str(e)}")
    
    def get_stock_analysis(self, ticker, discount_rate=0.125):
        """
        Get comprehensive stock analysis including price history, eight pillars, 
        intrinsic value, and financial statements
        """
        try:
            ticker = ticker.upper().strip()
            stock = Ticker(ticker)
            
            # Get basic data
            company_info = stock.info
            price_history = stock.price_history
            eight_pillars = stock.eight_pillars  # Get actual eight pillars analysis
            intrinsic_value_df = stock.intrinsic_value(discount_rate)
            
            # Create price chart
            chart_html = self._create_price_chart(ticker, price_history)
            
            # Process eight pillars
            eight_pillars_html, eight_pillars_score = self._process_eight_pillars(eight_pillars)
            
            # Process intrinsic value
            intrinsic_value_html, valuation_recommendation = self._process_intrinsic_value(
                ticker, intrinsic_value_df, company_info
            )
            
            # Get financial statements
            financial_statements = self._get_financial_statements(stock)
            
            # Get financial ratios
            financial_ratios = self._get_financial_ratios(stock)
            
            return {
                'success': True,
                'ticker': ticker,
                'company_info': company_info,
                'chart_html': chart_html,
                'eight_pillars_html': eight_pillars_html,
                'eight_pillars_score': eight_pillars_score,
                'intrinsic_value_html': intrinsic_value_html,
                'valuation_recommendation': valuation_recommendation,
                'financial_statements': financial_statements,
                'financial_ratios': financial_ratios
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'ticker': ticker
            }
    
    def compare_stocks(self, tickers_list, discount_rate=0.125):
        """Compare multiple stocks across various metrics"""
        try:
            # Parse and validate tickers
            tickers = [t.strip().upper() for t in tickers_list if t.strip()]
            
            if len(tickers) > 10:
                tickers = tickers[:10]  # Limit to 10 stocks
            
            # Get comparison data
            stocks = Tickers(tickers)
            price_history = stocks.price_history
            eight_pillars_values = stocks.eight_pillars_values
            eight_pillars_marks = stocks.eight_pillars_marks
            
            # Create price comparison chart
            price_chart_html = self._create_price_comparison_chart(price_history)
            
            # Process eight pillars comparison
            eight_pillars_comparison = self._process_eight_pillars_comparison(
                eight_pillars_marks, eight_pillars_values
            )
            
            # Get intrinsic values comparison
            intrinsic_value_html, valuation_summary = self._get_intrinsic_values_comparison(
                tickers, discount_rate
            )
            
            # Create key metrics comparison
            key_metrics_html = self._create_key_metrics_comparison(tickers)
            
            return {
                'success': True,
                'tickers': tickers,
                'price_chart_html': price_chart_html,
                'eight_pillars_comparison': eight_pillars_comparison,
                'intrinsic_value_html': intrinsic_value_html,
                'valuation_summary': valuation_summary,
                'key_metrics_html': key_metrics_html
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def screen_stocks(self, criteria):
        """Screen stocks based on provided criteria"""
        try:
            # Use the real stock screener function
            screener_results = real_stock_screener(
                market_cap_min=criteria.get('market_cap_min'),
                market_cap_max=criteria.get('market_cap_max'),
                pe_ratio_max=criteria.get('pe_ratio_max'),
                price_book_max=criteria.get('price_book_max'),
                debt_to_equity_max=criteria.get('debt_to_equity_max'),
                roe_min=criteria.get('roe_min'),
                sector=criteria.get('sector') if criteria.get('sector') else None,
                min_pillars_score=criteria.get('min_pillars_score')
            )
            
            # Convert DataFrame to list of dictionaries
            filtered_stocks = []
            if not screener_results.empty:
                for _, row in screener_results.iterrows():
                    # Convert formatted market cap string back to numeric value
                    market_cap_str = row['Market Cap']
                    market_cap_numeric = None
                    if market_cap_str and isinstance(market_cap_str, str):
                        # Extract numeric value from formatted string like "$153,577M"
                        import re
                        match = re.search(r'\$([0-9,]+)M', market_cap_str)
                        if match:
                            market_cap_numeric = float(match.group(1).replace(',', ''))
                    
                    filtered_stocks.append({
                        'symbol': row['Symbol'],
                        'company_name': row['Company Name'],
                        'sector': row['Sector'],
                        'market_cap': market_cap_numeric,
                        'market_cap_display': market_cap_str,
                        'pe_ratio': row['P/E Ratio'],
                        'price_book': row['Price/Book'],
                        'roe': row['ROE (%)'],
                        'debt_equity': row['Debt/Equity'],
                        'pillars_score': row['Pillars Score']
                    })
            
            return {
                'success': True,
                'results': filtered_stocks,
                'count': len(filtered_stocks)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_stock_price(self, ticker):
        """Get current stock price"""
        try:
            stock = Ticker(ticker.upper())
            info = stock.info
            if not info.empty and 'Current Price' in info.index:
                price = float(info.loc['Current Price', 'Value'])
                return {
                    'success': True,
                    'price': price,
                    'ticker': ticker.upper()
                }
            else:
                return {
                    'success': False,
                    'error': 'Price not found'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_price_chart(self, ticker, price_history):
        """Create price history chart"""
        if price_history.empty:
            return None
        
        fig = px.line(x=price_history.index, y=price_history.values, 
                     title=f'{ticker} Price History',
                     labels={'x': 'Date', 'y': 'Price ($)'})
        fig.update_layout(showlegend=False)
        return fig.to_html(full_html=False, include_plotlyjs=False)
    
    def _create_price_comparison_chart(self, price_history):
        """Create price comparison chart for multiple stocks"""
        if price_history.empty:
            return None
        
        fig = go.Figure()
        for ticker in price_history.columns:
            fig.add_trace(go.Scatter(
                x=price_history.index,
                y=price_history[ticker],
                mode='lines',
                name=ticker
            ))
        fig.update_layout(
            title='Price History Comparison',
            xaxis_title='Date',
            yaxis_title='Price ($)',
            hovermode='x unified'
        )
        return fig.to_html(full_html=False, include_plotlyjs=False)
    
    def _process_eight_pillars(self, eight_pillars):
        """Process eight pillars data"""
        if eight_pillars.empty:
            return None, 0
        
        eight_pillars_html = eight_pillars.to_html(classes='table table-striped table-hover', escape=False)
        eight_pillars_score = calculate_eight_pillars_score(eight_pillars)
        return eight_pillars_html, eight_pillars_score
    
    def _process_eight_pillars_comparison(self, eight_pillars_marks, eight_pillars_values):
        """Process eight pillars comparison data"""
        comparison = {}
        
        if not eight_pillars_marks.empty:
            comparison['marks_html'] = eight_pillars_marks.to_html(
                classes='table table-striped table-hover', escape=False
            )
            
            # Calculate scores for each ticker
            scores = {}
            for ticker in eight_pillars_marks.columns:
                marks = eight_pillars_marks[ticker]
                scores[ticker] = sum(1 for mark in marks if mark == "✔️")
            comparison['scores'] = scores
        
        if not eight_pillars_values.empty:
            comparison['values_html'] = eight_pillars_values.to_html(
                classes='table table-striped table-hover'
            )
        
        return comparison
    
    def _process_intrinsic_value(self, ticker, intrinsic_value_df, company_info):
        """Process intrinsic value data"""
        if intrinsic_value_df.empty:
            return None, None
        
        formatted_intrinsic = format_financial_dataframe(intrinsic_value_df)
        intrinsic_value_html = formatted_intrinsic.to_html(
            classes='table table-striped table-hover', escape=False
        )
        
        # Get valuation recommendation
        valuation_recommendation = None
        if ticker in intrinsic_value_df.columns:
            current_price = safe_float(company_info.get('last_close') if not company_info.empty else None)
            intrinsic_val = safe_float(
                intrinsic_value_df.loc['Intrinsic Value', ticker] 
                if 'Intrinsic Value' in intrinsic_value_df.index else None
            )
            valuation_recommendation = get_valuation_recommendation(current_price, intrinsic_val)
        
        return intrinsic_value_html, valuation_recommendation
    
    def _get_intrinsic_values_comparison(self, tickers, discount_rate):
        """Get intrinsic values for comparison"""
        try:
            intrinsic_data = []
            for ticker in tickers:
                stock = Ticker(ticker)
                iv_df = stock.intrinsic_value(discount_rate)
                if not iv_df.empty and ticker in iv_df.columns:
                    intrinsic_data.append(iv_df[ticker])
            
            if not intrinsic_data:
                return None, []
            
            combined_iv = pd.concat(intrinsic_data, axis=1)
            combined_iv.columns = tickers[:len(intrinsic_data)]
            intrinsic_value_html = combined_iv.to_html(classes='table table-striped table-hover')
            
            # Create valuation summary
            valuation_summary = []
            for ticker in combined_iv.columns:
                if 'Current Price' in combined_iv.index and 'Intrinsic Value' in combined_iv.index:
                    current_price = safe_float(combined_iv.loc['Current Price', ticker])
                    intrinsic_val = safe_float(combined_iv.loc['Intrinsic Value', ticker])
                    recommendation = get_valuation_recommendation(current_price, intrinsic_val)
                    if recommendation:
                        valuation_summary.append({
                            'ticker': ticker,
                            'class': getattr(recommendation, 'class'),
                            'message': recommendation.message
                        })
            
            return intrinsic_value_html, valuation_summary
            
        except Exception as e:
            print(f"Error processing intrinsic values: {e}")
            return None, []
    
    def _create_key_metrics_comparison(self, tickers):
        """Create key metrics comparison table"""
        key_metrics_data = []
        for ticker in tickers:
            try:
                stock = Ticker(ticker)
                info = stock.info
                if not info.empty:
                    key_metrics_data.append({
                        'Ticker': ticker,
                        'Company': info.get('comp_name_2', 'N/A'),
                        'Sector': info.get('zacks_x_sector_desc', 'N/A'),
                        'Last Price': f"${safe_float(info.get('last_close')):.2f}",
                        'Forward P/E': f"{safe_float(info.get('forward_pe_ratio')):.2f}",
                        'EPS Estimate': f"{safe_float(info.get('eps_mean_est_fr2')):.2f}"
                    })
            except:
                continue
        
        if not key_metrics_data:
            return None
        
        key_metrics_df = pd.DataFrame(key_metrics_data)
        return key_metrics_df.to_html(classes='table table-striped table-hover', index=False)
    
    def _get_financial_statements(self, stock):
        """Get formatted financial statements"""
        financial_statements = {}
        
        if not stock.income_statement_annual.empty:
            formatted_income = format_financial_dataframe(stock.income_statement_annual)
            financial_statements['income'] = formatted_income.to_html(
                classes='table table-striped table-hover', escape=False
            )
        else:
            financial_statements['income'] = '<p class="text-muted">No data available</p>'
        
        if not stock.balance_sheet_annual.empty:
            formatted_balance = format_financial_dataframe(stock.balance_sheet_annual)
            financial_statements['balance'] = formatted_balance.to_html(
                classes='table table-striped table-hover', escape=False
            )
        else:
            financial_statements['balance'] = '<p class="text-muted">No data available</p>'
        
        if not stock.cash_flow_annual.empty:
            formatted_cashflow = format_financial_dataframe(stock.cash_flow_annual)
            financial_statements['cashflow'] = formatted_cashflow.to_html(
                classes='table table-striped table-hover', escape=False
            )
        else:
            financial_statements['cashflow'] = '<p class="text-muted">No data available</p>'
        
        return financial_statements
    
    def _get_financial_ratios(self, stock):
        """Get financial ratios"""
        return {
            'gross_margin': stock.gross_margin,
            'operating_margin': stock.operating_margin,
            'net_margin': stock.net_margin,
            'price_earnings': stock.price_earnings,
            'price_sales': stock.price_sales,
            'roe': stock.roe
        }


# Global instance
stock_service = StockService()