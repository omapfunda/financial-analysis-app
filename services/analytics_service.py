"""
Analytics Service - Centralized business logic for analytics and optimization
"""
from portfolio_analytics import PortfolioAnalytics
from portfolio_optimizer import get_portfolio_optimizer
from portfolio_manager import portfolio_manager
from utils.scoring import calculate_eight_pillars_score, calculate_financial_strength_score
from utils.recommendations import get_valuation_recommendation, get_risk_recommendation
from macrotrends_api import Ticker
import pandas as pd


class AnalyticsService:
    """Service class for analytics and optimization operations"""
    
    def __init__(self):
        self.portfolio_analytics = PortfolioAnalytics()
        self.portfolio_optimizer = get_portfolio_optimizer(portfolio_manager)
    
    def calculate_stock_scores(self, ticker):
        """Calculate various scores for a stock"""
        try:
            stock = Ticker(ticker.upper())
            
            # Get eight pillars score
            eight_pillars = stock.eight_pillars
            eight_pillars_score = 0
            if not eight_pillars.empty:
                eight_pillars_score = calculate_eight_pillars_score(eight_pillars)
            
            # Calculate financial strength score
            financial_strength_score = calculate_financial_strength_score(stock)
            
            # Get risk recommendation
            risk_recommendation = get_risk_recommendation(stock)
            
            return {
                'success': True,
                'ticker': ticker.upper(),
                'eight_pillars_score': eight_pillars_score,
                'financial_strength_score': financial_strength_score,
                'risk_recommendation': risk_recommendation
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_portfolio_performance(self, portfolio_id):
        """Calculate comprehensive portfolio performance metrics"""
        try:
            performance = self.portfolio_analytics.calculate_portfolio_performance(portfolio_id)
            return {
                'success': True,
                'data': performance
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_sector_allocation(self, portfolio_id):
        """Get portfolio sector allocation analysis"""
        try:
            sector_allocation = self.portfolio_analytics.get_sector_allocation(portfolio_id)
            return {
                'success': True,
                'data': sector_allocation
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_risk_metrics(self, portfolio_id):
        """Calculate portfolio risk metrics"""
        try:
            risk_metrics = self.portfolio_analytics.calculate_risk_metrics(portfolio_id)
            return {
                'success': True,
                'data': risk_metrics
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_correlation_matrix(self, portfolio_id):
        """Get portfolio correlation matrix"""
        try:
            correlation_matrix = self.portfolio_analytics.get_correlation_matrix(portfolio_id)
            return {
                'success': True,
                'data': correlation_matrix
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def optimize_portfolio(self, portfolio_id):
        """Perform portfolio optimization"""
        try:
            if not self.portfolio_optimizer:
                return {
                    'success': False,
                    'error': 'Portfolio optimization requires PyPortfolioOpt. Please install it first.'
                }
            
            optimization_results = self.portfolio_optimizer.calculate_efficient_frontier(portfolio_id)
            
            if 'error' in optimization_results:
                return {
                    'success': False,
                    'error': optimization_results['error']
                }
            
            return {
                'success': True,
                'data': optimization_results
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_portfolio_efficiency(self, portfolio_id):
        """Analyze portfolio efficiency"""
        try:
            if not self.portfolio_optimizer:
                return {
                    'success': False,
                    'error': 'PyPortfolioOpt not available'
                }
            
            efficiency_analysis = self.portfolio_optimizer.analyze_portfolio_efficiency(portfolio_id)
            return {
                'success': True,
                'data': efficiency_analysis
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_rebalancing_recommendations(self, portfolio_id, strategy='max_sharpe'):
        """Get portfolio rebalancing recommendations"""
        try:
            if not self.portfolio_optimizer:
                return {
                    'success': False,
                    'error': 'PyPortfolioOpt not available'
                }
            
            rebalancing = self.portfolio_optimizer.rebalance_portfolio(portfolio_id, strategy)
            return {
                'success': True,
                'data': rebalancing
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def compare_portfolios(self, portfolio_ids):
        """Compare multiple portfolios"""
        try:
            comparison_data = []
            
            for portfolio_id in portfolio_ids:
                # Get basic portfolio info
                portfolio = portfolio_manager.get_portfolio(portfolio_id)
                if not portfolio:
                    continue
                
                # Get performance metrics
                performance = self.portfolio_analytics.calculate_portfolio_performance(portfolio_id)
                risk_metrics = self.portfolio_analytics.calculate_risk_metrics(portfolio_id)
                portfolio_value = portfolio_manager.get_portfolio_value(portfolio_id)
                
                comparison_data.append({
                    'portfolio_id': portfolio_id,
                    'name': portfolio.get('name', 'Unknown'),
                    'total_value': portfolio_value.get('total_value', 0) if portfolio_value else 0,
                    'performance': performance,
                    'risk_metrics': risk_metrics
                })
            
            return {
                'success': True,
                'data': comparison_data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_investment_recommendations(self, portfolio_id):
        """Generate investment recommendations for a portfolio"""
        try:
            portfolio = portfolio_manager.get_portfolio(portfolio_id)
            if not portfolio:
                return {
                    'success': False,
                    'error': 'Portfolio not found'
                }
            
            recommendations = []
            
            # Get current holdings
            holdings = portfolio.get('holdings', {})
            
            # Analyze each holding
            for ticker, holding_data in holdings.items():
                try:
                    stock = Ticker(ticker)
                    
                    # Get current price and intrinsic value
                    info = stock.info
                    intrinsic_value_df = stock.intrinsic_value()
                    
                    if not info.empty and not intrinsic_value_df.empty:
                        current_price = info.get('last_close')
                        if ticker in intrinsic_value_df.columns and 'Intrinsic Value' in intrinsic_value_df.index:
                            intrinsic_val = intrinsic_value_df.loc['Intrinsic Value', ticker]
                            
                            # Get valuation recommendation
                            valuation_rec = get_valuation_recommendation(current_price, intrinsic_val)
                            
                            if valuation_rec:
                                recommendations.append({
                                    'ticker': ticker,
                                    'current_price': current_price,
                                    'intrinsic_value': intrinsic_val,
                                    'recommendation': valuation_rec,
                                    'shares_held': holding_data.get('shares', 0),
                                    'position_value': holding_data.get('shares', 0) * current_price
                                })
                except:
                    continue
            
            # Sort recommendations by potential upside
            recommendations.sort(key=lambda x: x.get('intrinsic_value', 0) / x.get('current_price', 1), reverse=True)
            
            return {
                'success': True,
                'data': recommendations
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_diversification_metrics(self, portfolio_id):
        """Calculate portfolio diversification metrics"""
        try:
            portfolio = portfolio_manager.get_portfolio(portfolio_id)
            if not portfolio:
                return {
                    'success': False,
                    'error': 'Portfolio not found'
                }
            
            # Get sector allocation
            sector_allocation = self.portfolio_analytics.get_sector_allocation(portfolio_id)
            
            # Calculate diversification score
            diversification_score = 0
            if sector_allocation:
                # Simple diversification score based on sector distribution
                sector_weights = [item.get('percentage', 0) for item in sector_allocation]
                # Higher score for more even distribution
                if sector_weights:
                    max_weight = max(sector_weights)
                    diversification_score = max(0, 100 - max_weight)
            
            # Get correlation matrix for additional insights
            correlation_matrix = self.portfolio_analytics.get_correlation_matrix(portfolio_id)
            
            return {
                'success': True,
                'data': {
                    'diversification_score': diversification_score,
                    'sector_allocation': sector_allocation,
                    'correlation_matrix': correlation_matrix,
                    'recommendations': self._get_diversification_recommendations(sector_allocation)
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_diversification_recommendations(self, sector_allocation):
        """Generate diversification recommendations"""
        if not sector_allocation:
            return []
        
        recommendations = []
        
        # Find overweight sectors (>30%)
        for sector in sector_allocation:
            if sector.get('percentage', 0) > 30:
                recommendations.append({
                    'type': 'reduce',
                    'sector': sector.get('name', 'Unknown'),
                    'current_weight': sector.get('percentage', 0),
                    'message': f"Consider reducing exposure to {sector.get('name', 'Unknown')} sector (currently {sector.get('percentage', 0):.1f}%)"
                })
        
        # Check if portfolio is too concentrated
        if len(sector_allocation) < 5:
            recommendations.append({
                'type': 'diversify',
                'message': f"Portfolio is concentrated in only {len(sector_allocation)} sectors. Consider adding exposure to other sectors."
            })
        
        return recommendations


# Global instance
analytics_service = AnalyticsService()