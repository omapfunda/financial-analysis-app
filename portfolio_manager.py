#!/usr/bin/env python3
"""
Portfolio Management System
Handles portfolio creation, storage, and analytics for the financial analysis application.
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from macrotrends_api import Ticker
from cache_manager import app_cache

class PortfolioManager:
    """Manages portfolio data storage and operations"""
    
    def __init__(self, data_file: str = "portfolios.json"):
        self.data_file = data_file
        self.portfolios = self._load_portfolios()
    
    def _load_portfolios(self) -> Dict:
        """Load portfolios from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def _save_portfolios(self):
        """Save portfolios to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.portfolios, f, indent=2, default=str)
    
    def create_portfolio(self, name: str, description: str = "", initial_cash: float = 10000.0) -> str:
        """Create a new portfolio"""
        portfolio_id = str(uuid.uuid4())
        portfolio = {
            "id": portfolio_id,
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "initial_cash": initial_cash,
            "current_cash": initial_cash,
            "holdings": {},  # {ticker: {"shares": float, "avg_price": float, "purchase_date": str}}
            "transactions": []  # List of buy/sell transactions
        }
        
        self.portfolios[portfolio_id] = portfolio
        self._save_portfolios()
        return portfolio_id
    
    def get_portfolio(self, portfolio_id: str) -> Optional[Dict]:
        """Get portfolio by ID"""
        return self.portfolios.get(portfolio_id)
    
    def get_all_portfolios(self) -> Dict:
        """Get all portfolios"""
        return self.portfolios
    
    def update_portfolio(self, portfolio_id: str, name: str = None, description: str = None) -> bool:
        """Update portfolio metadata"""
        if portfolio_id not in self.portfolios:
            return False
        
        portfolio = self.portfolios[portfolio_id]
        if name:
            portfolio["name"] = name
        if description is not None:
            portfolio["description"] = description
        portfolio["updated_at"] = datetime.now().isoformat()
        
        self._save_portfolios()
        return True
    
    def delete_portfolio(self, portfolio_id: str) -> bool:
        """Delete a portfolio"""
        if portfolio_id in self.portfolios:
            del self.portfolios[portfolio_id]
            self._save_portfolios()
            return True
        return False
    
    def add_holding(self, portfolio_id: str, ticker: str, shares: float, price: float) -> bool:
        """Add or update a holding in the portfolio"""
        if portfolio_id not in self.portfolios:
            return False
        
        portfolio = self.portfolios[portfolio_id]
        total_cost = shares * price
        
        # Check if we have enough cash
        if total_cost > portfolio["current_cash"]:
            return False
        
        # Update cash
        portfolio["current_cash"] -= total_cost
        
        # Add transaction
        transaction = {
            "id": str(uuid.uuid4()),
            "type": "buy",
            "ticker": ticker,
            "shares": shares,
            "price": price,
            "total": total_cost,
            "date": datetime.now().isoformat()
        }
        portfolio["transactions"].append(transaction)
        
        # Update holdings
        if ticker in portfolio["holdings"]:
            # Calculate new average price
            existing = portfolio["holdings"][ticker]
            total_shares = existing["shares"] + shares
            total_value = (existing["shares"] * existing["avg_price"]) + total_cost
            new_avg_price = total_value / total_shares
            
            portfolio["holdings"][ticker] = {
                "shares": total_shares,
                "avg_price": new_avg_price,
                "purchase_date": existing["purchase_date"]  # Keep original date
            }
        else:
            portfolio["holdings"][ticker] = {
                "shares": shares,
                "avg_price": price,
                "purchase_date": datetime.now().isoformat()
            }
        
        portfolio["updated_at"] = datetime.now().isoformat()
        self._save_portfolios()
        return True
    
    def remove_holding(self, portfolio_id: str, ticker: str, shares: float = None) -> bool:
        """Remove shares from a holding (sell)"""
        if portfolio_id not in self.portfolios:
            return False
        
        portfolio = self.portfolios[portfolio_id]
        if ticker not in portfolio["holdings"]:
            return False
        
        holding = portfolio["holdings"][ticker]
        shares_to_sell = shares if shares else holding["shares"]
        
        if shares_to_sell > holding["shares"]:
            return False
        
        # Get current price for the sale
        try:
            current_price = self._get_current_price(ticker)
            if current_price is None:
                return False
        except:
            return False
        
        total_proceeds = shares_to_sell * current_price
        
        # Add transaction
        transaction = {
            "id": str(uuid.uuid4()),
            "type": "sell",
            "ticker": ticker,
            "shares": shares_to_sell,
            "price": current_price,
            "total": total_proceeds,
            "date": datetime.now().isoformat()
        }
        portfolio["transactions"].append(transaction)
        
        # Update cash
        portfolio["current_cash"] += total_proceeds
        
        # Update holdings
        if shares_to_sell >= holding["shares"]:
            # Sell all shares
            del portfolio["holdings"][ticker]
        else:
            # Partial sale
            holding["shares"] -= shares_to_sell
        
        portfolio["updated_at"] = datetime.now().isoformat()
        self._save_portfolios()
        return True
    
    def _get_current_price(self, ticker: str) -> Optional[float]:
        """Get current price for a ticker"""
        cache_key = f"current_price_{ticker}"
        cached_price = app_cache.get(cache_key)
        
        if cached_price is not None:
            return cached_price
        
        try:
            stock = Ticker(ticker)
            info = stock.info
            if not info.empty and 'Current Price' in info.index:
                price = float(info.loc['Current Price', 'Value'])
                app_cache.set(cache_key, price, ttl=300)  # Cache for 5 minutes
                return price
        except:
            pass
        
        return None
    
    def get_portfolio_value(self, portfolio_id: str) -> Dict:
        """Calculate current portfolio value and performance"""
        if portfolio_id not in self.portfolios:
            return {}
        
        portfolio = self.portfolios[portfolio_id]
        holdings_value = 0.0
        holdings_details = []
        
        for ticker, holding in portfolio["holdings"].items():
            current_price = self._get_current_price(ticker)
            if current_price:
                market_value = holding["shares"] * current_price
                cost_basis = holding["shares"] * holding["avg_price"]
                gain_loss = market_value - cost_basis
                gain_loss_pct = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0
                
                holdings_details.append({
                    "ticker": ticker,
                    "shares": holding["shares"],
                    "avg_price": holding["avg_price"],
                    "current_price": current_price,
                    "cost_basis": cost_basis,
                    "market_value": market_value,
                    "gain_loss": gain_loss,
                    "gain_loss_pct": gain_loss_pct,
                    "purchase_date": holding["purchase_date"]
                })
                
                holdings_value += market_value
        
        total_value = holdings_value + portfolio["current_cash"]
        total_return = total_value - portfolio["initial_cash"]
        total_return_pct = (total_return / portfolio["initial_cash"] * 100) if portfolio["initial_cash"] > 0 else 0
        
        return {
            "portfolio_id": portfolio_id,
            "name": portfolio["name"],
            "total_value": total_value,
            "holdings_value": holdings_value,
            "cash": portfolio["current_cash"],
            "initial_cash": portfolio["initial_cash"],
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "holdings": holdings_details,
            "created_at": portfolio["created_at"],
            "updated_at": portfolio["updated_at"]
        }
    
    def get_portfolio_allocation(self, portfolio_id: str) -> List[Dict]:
        """Get portfolio allocation breakdown"""
        portfolio_value = self.get_portfolio_value(portfolio_id)
        if not portfolio_value or portfolio_value["total_value"] == 0:
            return []
        
        allocation = []
        total_value = portfolio_value["total_value"]
        
        # Add holdings allocation
        for holding in portfolio_value["holdings"]:
            allocation.append({
                "name": holding["ticker"],
                "value": holding["market_value"],
                "percentage": (holding["market_value"] / total_value) * 100,
                "type": "stock"
            })
        
        # Add cash allocation
        if portfolio_value["cash"] > 0:
            allocation.append({
                "name": "Cash",
                "value": portfolio_value["cash"],
                "percentage": (portfolio_value["cash"] / total_value) * 100,
                "type": "cash"
            })
        
        return sorted(allocation, key=lambda x: x["percentage"], reverse=True)

# Global portfolio manager instance
portfolio_manager = PortfolioManager()