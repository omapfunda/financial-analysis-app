"""
Portfolio Analytics Module
Provides advanced analytics and performance calculations for portfolios
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import yfinance as yf
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Container for portfolio performance metrics"""
    total_return: float
    total_return_pct: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    beta: float
    alpha: float
    var_95: float  # Value at Risk (95% confidence)
    
class PortfolioAnalytics:
    """Advanced portfolio analytics and performance calculations"""
    
    def __init__(self):
        self.benchmark_ticker = "SPY"  # S&P 500 ETF as benchmark
        
    def calculate_portfolio_performance(self, portfolio_data: Dict, 
                                      start_date: Optional[str] = None,
                                      end_date: Optional[str] = None) -> PerformanceMetrics:
        """
        Calculate comprehensive portfolio performance metrics
        
        Args:
            portfolio_data: Portfolio data with holdings
            start_date: Start date for analysis (YYYY-MM-DD)
            end_date: End date for analysis (YYYY-MM-DD)
            
        Returns:
            PerformanceMetrics object with calculated metrics
        """
        try:
            if not portfolio_data.get('holdings'):
                return self._empty_metrics()
                
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            # Get portfolio historical data
            portfolio_returns = self._calculate_portfolio_returns(
                portfolio_data, start_date, end_date
            )
            
            if portfolio_returns is None or len(portfolio_returns) < 2:
                return self._empty_metrics()
            
            # Get benchmark returns
            benchmark_returns = self._get_benchmark_returns(start_date, end_date)
            
            # Calculate metrics
            total_return = (portfolio_returns.iloc[-1] / portfolio_returns.iloc[0] - 1) * 100
            annualized_return = self._calculate_annualized_return(portfolio_returns)
            volatility = self._calculate_volatility(portfolio_returns)
            sharpe_ratio = self._calculate_sharpe_ratio(portfolio_returns)
            max_drawdown = self._calculate_max_drawdown(portfolio_returns)
            
            # Calculate beta and alpha if benchmark data available
            beta, alpha = 0.0, 0.0
            if benchmark_returns is not None and len(benchmark_returns) == len(portfolio_returns):
                beta, alpha = self._calculate_beta_alpha(portfolio_returns, benchmark_returns)
            
            # Calculate Value at Risk
            var_95 = self._calculate_var(portfolio_returns)
            
            return PerformanceMetrics(
                total_return=total_return,
                total_return_pct=total_return,
                annualized_return=annualized_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                beta=beta,
                alpha=alpha,
                var_95=var_95
            )
            
        except Exception as e:
            logger.error(f"Error calculating portfolio performance: {e}")
            return self._empty_metrics()
    
    def _calculate_portfolio_returns(self, portfolio_data: Dict, 
                                   start_date: str, end_date: str) -> Optional[pd.Series]:
        """Calculate historical portfolio returns"""
        try:
            holdings = portfolio_data.get('holdings', [])
            if not holdings:
                return None
            
            # Get price data for all holdings
            tickers = [holding['ticker'] for holding in holdings]
            weights = {}
            total_value = sum(holding['shares'] * holding['avg_cost'] for holding in holdings)
            
            for holding in holdings:
                position_value = holding['shares'] * holding['avg_cost']
                weights[holding['ticker']] = position_value / total_value if total_value > 0 else 0
            
            # Download historical data
            price_data = yf.download(tickers, start=start_date, end=end_date, progress=False)
            
            if price_data.empty:
                return None
            
            # Handle single ticker case
            if len(tickers) == 1:
                prices = price_data['Adj Close']
            else:
                prices = price_data['Adj Close']
            
            # Calculate weighted portfolio returns
            portfolio_values = []
            
            for date in prices.index:
                portfolio_value = 0
                for ticker in tickers:
                    if len(tickers) == 1:
                        price = prices.loc[date] if not pd.isna(prices.loc[date]) else 0
                    else:
                        price = prices.loc[date, ticker] if not pd.isna(prices.loc[date, ticker]) else 0
                    
                    portfolio_value += weights.get(ticker, 0) * price
                
                portfolio_values.append(portfolio_value)
            
            return pd.Series(portfolio_values, index=prices.index)
            
        except Exception as e:
            logger.error(f"Error calculating portfolio returns: {e}")
            return None
    
    def _get_benchmark_returns(self, start_date: str, end_date: str) -> Optional[pd.Series]:
        """Get benchmark (S&P 500) returns for comparison"""
        try:
            benchmark_data = yf.download(self.benchmark_ticker, start=start_date, 
                                       end=end_date, progress=False)
            if benchmark_data.empty:
                return None
            return benchmark_data['Adj Close']
        except Exception as e:
            logger.error(f"Error getting benchmark returns: {e}")
            return None
    
    def _calculate_annualized_return(self, returns: pd.Series) -> float:
        """Calculate annualized return"""
        try:
            if len(returns) < 2:
                return 0.0
            
            days = (returns.index[-1] - returns.index[0]).days
            if days <= 0:
                return 0.0
            
            total_return = returns.iloc[-1] / returns.iloc[0] - 1
            annualized = (1 + total_return) ** (365.25 / days) - 1
            return annualized * 100
        except:
            return 0.0
    
    def _calculate_volatility(self, returns: pd.Series) -> float:
        """Calculate annualized volatility"""
        try:
            if len(returns) < 2:
                return 0.0
            
            daily_returns = returns.pct_change().dropna()
            if len(daily_returns) == 0:
                return 0.0
            
            volatility = daily_returns.std() * np.sqrt(252)  # Annualized
            return volatility * 100
        except:
            return 0.0
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        try:
            if len(returns) < 2:
                return 0.0
            
            daily_returns = returns.pct_change().dropna()
            if len(daily_returns) == 0:
                return 0.0
            
            excess_returns = daily_returns.mean() * 252 - risk_free_rate  # Annualized
            volatility = daily_returns.std() * np.sqrt(252)
            
            if volatility == 0:
                return 0.0
            
            return excess_returns / volatility
        except:
            return 0.0
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        try:
            if len(returns) < 2:
                return 0.0
            
            # Calculate running maximum
            running_max = returns.expanding().max()
            drawdown = (returns - running_max) / running_max
            max_drawdown = drawdown.min()
            
            return abs(max_drawdown) * 100
        except:
            return 0.0
    
    def _calculate_beta_alpha(self, portfolio_returns: pd.Series, 
                            benchmark_returns: pd.Series) -> Tuple[float, float]:
        """Calculate portfolio beta and alpha relative to benchmark"""
        try:
            if len(portfolio_returns) < 2 or len(benchmark_returns) < 2:
                return 0.0, 0.0
            
            # Align the series
            aligned_data = pd.DataFrame({
                'portfolio': portfolio_returns,
                'benchmark': benchmark_returns
            }).dropna()
            
            if len(aligned_data) < 2:
                return 0.0, 0.0
            
            # Calculate returns
            portfolio_rets = aligned_data['portfolio'].pct_change().dropna()
            benchmark_rets = aligned_data['benchmark'].pct_change().dropna()
            
            if len(portfolio_rets) < 2 or len(benchmark_rets) < 2:
                return 0.0, 0.0
            
            # Calculate beta
            covariance = np.cov(portfolio_rets, benchmark_rets)[0][1]
            benchmark_variance = np.var(benchmark_rets)
            
            if benchmark_variance == 0:
                return 0.0, 0.0
            
            beta = covariance / benchmark_variance
            
            # Calculate alpha (annualized)
            portfolio_return = portfolio_rets.mean() * 252
            benchmark_return = benchmark_rets.mean() * 252
            risk_free_rate = 0.02  # 2% risk-free rate
            
            alpha = portfolio_return - (risk_free_rate + beta * (benchmark_return - risk_free_rate))
            
            return beta, alpha * 100
        except:
            return 0.0, 0.0
    
    def _calculate_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate Value at Risk at given confidence level"""
        try:
            if len(returns) < 2:
                return 0.0
            
            daily_returns = returns.pct_change().dropna()
            if len(daily_returns) == 0:
                return 0.0
            
            var = np.percentile(daily_returns, (1 - confidence) * 100)
            return abs(var) * 100
        except:
            return 0.0
    
    def _empty_metrics(self) -> PerformanceMetrics:
        """Return empty performance metrics"""
        return PerformanceMetrics(
            total_return=0.0,
            total_return_pct=0.0,
            annualized_return=0.0,
            volatility=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            beta=0.0,
            alpha=0.0,
            var_95=0.0
        )
    
    def calculate_sector_allocation(self, portfolio_data: Dict) -> Dict[str, float]:
        """Calculate portfolio allocation by sector"""
        try:
            holdings = portfolio_data.get('holdings', [])
            if not holdings:
                return {}
            
            # This is a simplified version - in practice, you'd want to 
            # fetch actual sector data from a financial API
            sector_mapping = {
                'AAPL': 'Technology',
                'MSFT': 'Technology', 
                'GOOGL': 'Technology',
                'AMZN': 'Consumer Discretionary',
                'TSLA': 'Consumer Discretionary',
                'JPM': 'Financial Services',
                'JNJ': 'Healthcare',
                'PG': 'Consumer Staples',
                'KO': 'Consumer Staples',
                'WMT': 'Consumer Staples'
            }
            
            sector_allocation = {}
            total_value = sum(holding['market_value'] for holding in holdings)
            
            for holding in holdings:
                sector = sector_mapping.get(holding['ticker'], 'Other')
                weight = (holding['market_value'] / total_value * 100) if total_value > 0 else 0
                
                if sector in sector_allocation:
                    sector_allocation[sector] += weight
                else:
                    sector_allocation[sector] = weight
            
            return sector_allocation
            
        except Exception as e:
            logger.error(f"Error calculating sector allocation: {e}")
            return {}
    
    def calculate_correlation_matrix(self, portfolio_data: Dict, 
                                   period: str = "1y") -> Optional[pd.DataFrame]:
        """Calculate correlation matrix between portfolio holdings"""
        try:
            holdings = portfolio_data.get('holdings', [])
            if len(holdings) < 2:
                return None
            
            tickers = [holding['ticker'] for holding in holdings]
            
            # Download price data
            end_date = datetime.now()
            if period == "1y":
                start_date = end_date - timedelta(days=365)
            elif period == "6m":
                start_date = end_date - timedelta(days=180)
            elif period == "3m":
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=365)
            
            price_data = yf.download(tickers, start=start_date, end=end_date, progress=False)
            
            if price_data.empty:
                return None
            
            # Calculate returns
            if len(tickers) == 1:
                returns = price_data['Adj Close'].pct_change().dropna()
                return pd.DataFrame([[1.0]], index=tickers, columns=tickers)
            else:
                returns = price_data['Adj Close'].pct_change().dropna()
            
            # Calculate correlation matrix
            correlation_matrix = returns.corr()
            return correlation_matrix
            
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {e}")
            return None