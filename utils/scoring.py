"""
Scoring calculation utilities
"""
import pandas as pd


def calculate_eight_pillars_score(eight_pillars_df):
    """Calculate the score from eight pillars marks"""
    if eight_pillars_df.empty or 'Mark' not in eight_pillars_df.columns:
        return 0
    
    marks = eight_pillars_df['Mark']
    return sum(1 for mark in marks if mark == "✔️")


def calculate_financial_strength_score(financial_data):
    """Calculate financial strength score based on key metrics"""
    if not financial_data:
        return 0
    
    score = 0
    max_score = 10
    
    # Example scoring criteria (can be expanded)
    try:
        # Debt to equity ratio (lower is better)
        debt_to_equity = financial_data.get('debt_to_equity', 0)
        if debt_to_equity < 0.3:
            score += 2
        elif debt_to_equity < 0.6:
            score += 1
        
        # Current ratio (higher is better, but not too high)
        current_ratio = financial_data.get('current_ratio', 0)
        if 1.5 <= current_ratio <= 3.0:
            score += 2
        elif 1.0 <= current_ratio < 1.5:
            score += 1
        
        # ROE (higher is better)
        roe = financial_data.get('roe', 0)
        if roe > 15:
            score += 2
        elif roe > 10:
            score += 1
        
        # Revenue growth (positive is good)
        revenue_growth = financial_data.get('revenue_growth', 0)
        if revenue_growth > 10:
            score += 2
        elif revenue_growth > 5:
            score += 1
        
        # Profit margin (higher is better)
        profit_margin = financial_data.get('profit_margin', 0)
        if profit_margin > 20:
            score += 2
        elif profit_margin > 10:
            score += 1
            
    except (KeyError, TypeError, ValueError):
        pass
    
    return min(score, max_score)  # Cap at max_score