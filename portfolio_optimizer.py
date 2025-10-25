#!/usr/bin/env python3
"""
Portfolio Optimization Module
Uses PyPortfolioOpt for modern portfolio theory optimization
"""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    from pypfopt import EfficientFrontier, risk_models, expected_returns
    from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices
    from pypfopt.plotting import plot_efficient_frontier
    PYPFOPT_AVAILABLE = True
except ImportError:
    PYPFOPT_AVAILABLE = False

class PortfolioOptimizer:
    """Portfolio optimization using Modern Portfolio Theory"""
    
    def __init__(self, portfolio_manager):
        self.portfolio_manager = portfolio_manager
        if not PYPFOPT_AVAILABLE:
            raise ImportError("PyPortfolioOpt is required. Install with: pip install PyPortfolioOpt")
    
    def get_portfolio_tickers(self, portfolio_id: str) -> List[str]:
        """Get list of tickers in portfolio"""
        portfolio = self.portfolio_manager.get_portfolio(portfolio_id)
        if not portfolio or not portfolio.get('holdings'):
            return []
        return list(portfolio['holdings'].keys())
    
    def get_historical_data(self, tickers: List[str], period: str = "2y") -> pd.DataFrame:
        """Get historical price data for tickers"""
        if not tickers:
            return pd.DataFrame()
        
        try:
            data = yf.download(tickers, period=period, progress=False)['Adj Close']
            if isinstance(data, pd.Series):
                data = data.to_frame(tickers[0])
            return data.dropna()
        except Exception as e:
            print(f"Error downloading data: {e}")
            return pd.DataFrame()
    
    def calculate_efficient_frontier(self, portfolio_id: str, risk_free_rate: float = 0.02) -> Dict:
        """Calculate efficient frontier for portfolio"""
        tickers = self.get_portfolio_tickers(portfolio_id)
        if len(tickers) < 2:
            return {"error": "Need at least 2 stocks for optimization"}
        
        # Get historical data
        prices = self.get_historical_data(tickers)
        if prices.empty:
            return {"error": "Could not retrieve historical data"}
        
        try:
            # Calculate expected returns and covariance matrix
            mu = expected_returns.mean_historical_return(prices)
            S = risk_models.sample_cov(prices)
            
            # Create efficient frontier
            ef = EfficientFrontier(mu, S)
            
            # Calculate different optimization strategies
            results = {}
            
            # 1. Maximum Sharpe ratio
            ef_max_sharpe = EfficientFrontier(mu, S)
            weights_max_sharpe = ef_max_sharpe.max_sharpe(risk_free_rate=risk_free_rate)
            cleaned_weights_sharpe = ef_max_sharpe.clean_weights()
            performance_sharpe = ef_max_sharpe.portfolio_performance(risk_free_rate=risk_free_rate)
            
            results['max_sharpe'] = {
                'weights': cleaned_weights_sharpe,
                'expected_return': performance_sharpe[0],
                'volatility': performance_sharpe[1],
                'sharpe_ratio': performance_sharpe[2]
            }
            
            # 2. Minimum volatility
            ef_min_vol = EfficientFrontier(mu, S)
            weights_min_vol = ef_min_vol.min_volatility()
            cleaned_weights_vol = ef_min_vol.clean_weights()
            performance_vol = ef_min_vol.portfolio_performance(risk_free_rate=risk_free_rate)
            
            results['min_volatility'] = {
                'weights': cleaned_weights_vol,
                'expected_return': performance_vol[0],
                'volatility': performance_vol[1],
                'sharpe_ratio': performance_vol[2]
            }
            
            # 3. Efficient return (target 12% annual return)
            try:
                ef_efficient = EfficientFrontier(mu, S)
                weights_efficient = ef_efficient.efficient_return(target_return=0.12)
                cleaned_weights_efficient = ef_efficient.clean_weights()
                performance_efficient = ef_efficient.portfolio_performance(risk_free_rate=risk_free_rate)
                
                results['efficient_return'] = {
                    'weights': cleaned_weights_efficient,
                    'expected_return': performance_efficient[0],
                    'volatility': performance_efficient[1],
                    'sharpe_ratio': performance_efficient[2]
                }
            except:
                # If 12% return is not achievable, skip this optimization
                pass
            
            # 4. Equal weights for comparison
            n_assets = len(tickers)
            equal_weights = {ticker: 1/n_assets for ticker in tickers}
            
            # Calculate performance for equal weights
            equal_returns = sum(mu[ticker] * (1/n_assets) for ticker in tickers)
            equal_variance = np.dot(np.array([1/n_assets] * n_assets), 
                                  np.dot(S.values, np.array([1/n_assets] * n_assets)))
            equal_volatility = np.sqrt(equal_variance)
            equal_sharpe = (equal_returns - risk_free_rate) / equal_volatility
            
            results['equal_weights'] = {
                'weights': equal_weights,
                'expected_return': equal_returns,
                'volatility': equal_volatility,
                'sharpe_ratio': equal_sharpe
            }
            
            return results
            
        except Exception as e:
            return {"error": f"Optimization failed: {str(e)}"}
    
    def get_discrete_allocation(self, weights: Dict[str, float], total_portfolio_value: float) -> Dict:
        """Convert optimal weights to discrete share allocation"""
        tickers = list(weights.keys())
        
        try:
            # Get latest prices
            latest_prices = get_latest_prices(yf.download(tickers, period="5d", progress=False)['Adj Close'])
            
            # Calculate discrete allocation
            da = DiscreteAllocation(weights, latest_prices, total_portfolio_value=total_portfolio_value)
            allocation, leftover = da.greedy_portfolio()
            
            return {
                'allocation': allocation,
                'leftover_cash': leftover,
                'total_value': total_portfolio_value
            }
            
        except Exception as e:
            return {"error": f"Allocation calculation failed: {str(e)}"}
    
    def rebalance_portfolio(self, portfolio_id: str, strategy: str = "max_sharpe") -> Dict:
        """Generate rebalancing recommendations"""
        portfolio_value = self.portfolio_manager.get_portfolio_value(portfolio_id)
        if not portfolio_value:
            return {"error": "Portfolio not found"}
        
        # Get current allocation
        current_allocation = {}
        total_value = portfolio_value['total_value']
        
        for holding in portfolio_value['holdings']:
            current_allocation[holding['ticker']] = holding['market_value'] / total_value
        
        # Get optimal allocation
        optimization_results = self.calculate_efficient_frontier(portfolio_id)
        if 'error' in optimization_results:
            return optimization_results
        
        if strategy not in optimization_results:
            return {"error": f"Strategy '{strategy}' not available"}
        
        optimal_weights = optimization_results[strategy]['weights']
        
        # Calculate rebalancing actions
        rebalancing_actions = []
        
        for ticker in set(list(current_allocation.keys()) + list(optimal_weights.keys())):
            current_weight = current_allocation.get(ticker, 0)
            optimal_weight = optimal_weights.get(ticker, 0)
            weight_diff = optimal_weight - current_weight
            
            if abs(weight_diff) > 0.01:  # Only suggest changes > 1%
                current_value = current_weight * total_value
                optimal_value = optimal_weight * total_value
                value_diff = optimal_value - current_value
                
                action = {
                    'ticker': ticker,
                    'current_weight': current_weight,
                    'optimal_weight': optimal_weight,
                    'weight_difference': weight_diff,
                    'current_value': current_value,
                    'optimal_value': optimal_value,
                    'value_difference': value_diff,
                    'action': 'buy' if value_diff > 0 else 'sell'
                }
                rebalancing_actions.append(action)
        
        return {
            'strategy': strategy,
            'current_allocation': current_allocation,
            'optimal_allocation': optimal_weights,
            'rebalancing_actions': rebalancing_actions,
            'expected_performance': optimization_results[strategy]
        }
    
    def analyze_portfolio_efficiency(self, portfolio_id: str) -> Dict:
        """Analyze how efficient the current portfolio is"""
        portfolio_value = self.portfolio_manager.get_portfolio_value(portfolio_id)
        if not portfolio_value:
            return {"error": "Portfolio not found"}
        
        tickers = [holding['ticker'] for holding in portfolio_value['holdings']]
        if len(tickers) < 2:
            return {"error": "Need at least 2 stocks for efficiency analysis"}
        
        # Get current weights
        total_value = portfolio_value['total_value']
        current_weights = {}
        for holding in portfolio_value['holdings']:
            current_weights[holding['ticker']] = holding['market_value'] / total_value
        
        # Get historical data and calculate metrics
        prices = self.get_historical_data(tickers)
        if prices.empty:
            return {"error": "Could not retrieve historical data"}
        
        try:
            mu = expected_returns.mean_historical_return(prices)
            S = risk_models.sample_cov(prices)
            
            # Calculate current portfolio performance
            current_return = sum(mu[ticker] * weight for ticker, weight in current_weights.items())
            current_variance = np.dot(list(current_weights.values()), 
                                    np.dot(S.values, list(current_weights.values())))
            current_volatility = np.sqrt(current_variance)
            current_sharpe = (current_return - 0.02) / current_volatility
            
            # Get optimal portfolios
            optimization_results = self.calculate_efficient_frontier(portfolio_id)
            
            if 'error' in optimization_results:
                return optimization_results
            
            # Compare with optimal portfolios
            efficiency_analysis = {
                'current_portfolio': {
                    'expected_return': current_return,
                    'volatility': current_volatility,
                    'sharpe_ratio': current_sharpe,
                    'weights': current_weights
                },
                'optimal_portfolios': optimization_results,
                'efficiency_score': None,
                'recommendations': []
            }
            
            # Calculate efficiency score (how close to max Sharpe)
            max_sharpe_ratio = optimization_results.get('max_sharpe', {}).get('sharpe_ratio', 0)
            if max_sharpe_ratio > 0:
                efficiency_score = (current_sharpe / max_sharpe_ratio) * 100
                efficiency_analysis['efficiency_score'] = min(100, max(0, efficiency_score))
            
            # Generate recommendations
            if current_sharpe < max_sharpe_ratio * 0.8:  # If current Sharpe is < 80% of optimal
                efficiency_analysis['recommendations'].append(
                    "Consider rebalancing to improve risk-adjusted returns"
                )
            
            if current_volatility > optimization_results.get('min_volatility', {}).get('volatility', float('inf')):
                efficiency_analysis['recommendations'].append(
                    "Portfolio volatility could be reduced through better diversification"
                )
            
            return efficiency_analysis
            
        except Exception as e:
            return {"error": f"Efficiency analysis failed: {str(e)}"}

# Global optimizer instance
portfolio_optimizer = None

def get_portfolio_optimizer(portfolio_manager):
    """Get or create portfolio optimizer instance"""
    global portfolio_optimizer
    if portfolio_optimizer is None:
        try:
            portfolio_optimizer = PortfolioOptimizer(portfolio_manager)
        except ImportError:
            return None
    return portfolio_optimizer