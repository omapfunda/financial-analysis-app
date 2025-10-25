"""
Portfolio Service - Centralized business logic for portfolio operations
"""
from portfolio_manager import portfolio_manager
from portfolio_analytics import PortfolioAnalytics
from portfolio_optimizer import get_portfolio_optimizer
from utils.converters import safe_float
from macrotrends_api import Ticker


class PortfolioService:
    """Service class for portfolio-related operations"""
    
    def __init__(self):
        self.portfolio_manager = portfolio_manager
        self.analytics = PortfolioAnalytics()
        self.optimizer = get_portfolio_optimizer(portfolio_manager)
    
    def get_all_portfolios(self):
        """Get all portfolios with their summary information"""
        try:
            portfolios = self.portfolio_manager.get_all_portfolios()
            portfolio_summaries = []
            
            for portfolio_id, portfolio_data in portfolios.items():
                portfolio_value = self.portfolio_manager.get_portfolio_value(portfolio_id)
                if portfolio_value:
                    portfolio_summaries.append(portfolio_value)
            
            return {
                'success': True,
                'portfolios': portfolio_summaries
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_portfolio(self, name, description, initial_cash):
        """Create a new portfolio"""
        try:
            if not name.strip():
                return {
                    'success': False,
                    'error': 'Portfolio name is required'
                }
            
            portfolio_id = self.portfolio_manager.create_portfolio(
                name.strip(), description.strip(), safe_float(initial_cash, 10000)
            )
            
            return {
                'success': True,
                'portfolio_id': portfolio_id,
                'message': f'Portfolio "{name}" created successfully!'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_portfolio(self, portfolio_id):
        """Get portfolio details"""
        try:
            portfolio = self.portfolio_manager.get_portfolio(portfolio_id)
            if not portfolio:
                return {
                    'success': False,
                    'error': 'Portfolio not found'
                }
            
            portfolio_value = self.portfolio_manager.get_portfolio_value(portfolio_id)
            allocation = self.portfolio_manager.get_portfolio_allocation(portfolio_id)
            
            # Format allocation data
            allocation_data = []
            if allocation:
                for item in allocation:
                    allocation_data.append({
                        'name': item['name'],
                        'value': item['percentage'],
                        'type': item['type']
                    })
            
            return {
                'success': True,
                'portfolio': portfolio_value,
                'allocation': allocation_data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_portfolio(self, portfolio_id, name, description):
        """Update portfolio metadata"""
        try:
            if not name.strip():
                return {
                    'success': False,
                    'error': 'Portfolio name is required'
                }
            
            success = self.portfolio_manager.update_portfolio(
                portfolio_id, name.strip(), description.strip()
            )
            
            if success:
                return {
                    'success': True,
                    'message': 'Portfolio updated successfully!'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to update portfolio'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_portfolio(self, portfolio_id):
        """Delete a portfolio"""
        try:
            success = self.portfolio_manager.delete_portfolio(portfolio_id)
            if success:
                return {
                    'success': True,
                    'message': 'Portfolio deleted successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to delete portfolio'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_stock(self, portfolio_id, ticker, shares, price=None):
        """Add a stock to portfolio"""
        try:
            ticker = ticker.upper().strip()
            shares = safe_float(shares, 0)
            
            if not ticker or shares <= 0:
                return {
                    'success': False,
                    'error': 'Please provide valid ticker and shares'
                }
            
            # Get current price if not provided
            if price is None or safe_float(price, 0) <= 0:
                try:
                    stock = Ticker(ticker)
                    info = stock.info
                    if not info.empty and 'Current Price' in info.index:
                        price = float(info.loc['Current Price', 'Value'])
                    else:
                        return {
                            'success': False,
                            'error': 'Could not get current price for ticker'
                        }
                except:
                    return {
                        'success': False,
                        'error': 'Invalid ticker symbol'
                    }
            else:
                price = safe_float(price)
            
            success = self.portfolio_manager.add_holding(portfolio_id, ticker, shares, price)
            if success:
                return {
                    'success': True,
                    'message': f'Added {shares} shares of {ticker} at ${price:.2f}'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to add stock - insufficient cash or invalid data'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def remove_stock(self, portfolio_id, ticker, shares=None):
        """Remove/sell stock from portfolio"""
        try:
            ticker = ticker.upper().strip()
            if not ticker:
                return {
                    'success': False,
                    'error': 'Please provide a valid ticker'
                }
            
            shares_to_sell = safe_float(shares) if shares else None
            success = self.portfolio_manager.remove_holding(portfolio_id, ticker, shares_to_sell)
            
            if success:
                action = f"Sold {shares_to_sell} shares of {ticker}" if shares_to_sell else f"Sold all shares of {ticker}"
                return {
                    'success': True,
                    'message': action
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to sell stock - insufficient shares or invalid data'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_portfolio_value(self, portfolio_id):
        """Get portfolio value information"""
        try:
            portfolio_value = self.portfolio_manager.get_portfolio_value(portfolio_id)
            if portfolio_value:
                return {
                    'success': True,
                    'data': portfolio_value
                }
            else:
                return {
                    'success': False,
                    'error': 'Portfolio not found'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_portfolio_analytics(self, portfolio_id):
        """Get comprehensive portfolio analytics"""
        try:
            # Get all analytics data
            performance = self.analytics.calculate_portfolio_performance(portfolio_id)
            sector_allocation = self.analytics.get_sector_allocation(portfolio_id)
            risk_metrics = self.analytics.calculate_risk_metrics(portfolio_id)
            correlation_matrix = self.analytics.get_correlation_matrix(portfolio_id)
            
            return {
                'success': True,
                'data': {
                    'performance': performance,
                    'sector_allocation': sector_allocation,
                    'risk_metrics': risk_metrics,
                    'correlation_matrix': correlation_matrix
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_portfolio_performance(self, portfolio_id):
        """Get portfolio performance metrics"""
        try:
            performance = self.analytics.calculate_portfolio_performance(portfolio_id)
            return {
                'success': True,
                'data': performance
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_portfolio_risk_metrics(self, portfolio_id):
        """Get portfolio risk metrics"""
        try:
            risk_metrics = self.analytics.calculate_risk_metrics(portfolio_id)
            return {
                'success': True,
                'data': risk_metrics
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_portfolio_optimization(self, portfolio_id):
        """Get portfolio optimization results"""
        try:
            if not self.optimizer:
                return {
                    'success': False,
                    'error': 'Portfolio optimization requires PyPortfolioOpt. Please install it first.'
                }
            
            # Get optimization results
            optimization_results = self.optimizer.calculate_efficient_frontier(portfolio_id)
            
            if 'error' in optimization_results:
                return {
                    'success': False,
                    'error': optimization_results['error']
                }
            
            # Get efficiency analysis
            efficiency_analysis = self.optimizer.analyze_portfolio_efficiency(portfolio_id)
            
            # Get rebalancing recommendations
            rebalancing = self.optimizer.rebalance_portfolio(portfolio_id, 'max_sharpe')
            
            return {
                'success': True,
                'data': {
                    'optimization_results': optimization_results,
                    'efficiency_analysis': efficiency_analysis,
                    'rebalancing': rebalancing
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_rebalancing_recommendations(self, portfolio_id, strategy='max_sharpe'):
        """Get portfolio rebalancing recommendations"""
        try:
            if not self.optimizer:
                return {
                    'success': False,
                    'error': 'PyPortfolioOpt not available'
                }
            
            rebalancing = self.optimizer.rebalance_portfolio(portfolio_id, strategy)
            return {
                'success': True,
                'data': rebalancing
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_efficiency_analysis(self, portfolio_id):
        """Get portfolio efficiency analysis"""
        try:
            if not self.optimizer:
                return {
                    'success': False,
                    'error': 'PyPortfolioOpt not available'
                }
            
            efficiency_analysis = self.optimizer.analyze_portfolio_efficiency(portfolio_id)
            return {
                'success': True,
                'data': efficiency_analysis
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# Global instance
portfolio_service = PortfolioService()