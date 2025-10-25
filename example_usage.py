#!/usr/bin/env python3
"""
Example usage of the enhanced stock_screener function
"""

from macrotrends_api import stock_screener

def main():
    """Demonstrate various ways to use the stock_screener function"""
    
    print("=== Stock Screener Function Examples ===\n")
    
    # Example 1: Get all stocks (no filters)
    print("1. All available stocks:")
    all_stocks = stock_screener()
    print(f"   Found {len(all_stocks)} stocks")
    print()
    
    # Example 2: Filter by market cap and debt
    print("2. Large companies with low debt (Market Cap >= 1000M, Debt/Equity <= 1.0):")
    large_low_debt = stock_screener(market_cap_min=1000, debt_to_equity_max=1.0)
    print(f"   Found {len(large_low_debt)} stocks:")
    if not large_low_debt.empty:
        for _, stock in large_low_debt.iterrows():
            print(f"   - {stock['Symbol']}: {stock['Company Name']} (Market Cap: {stock['Market Cap']}, Debt/Equity: {stock['Debt/Equity']})")
    print()
    
    # Example 3: Sector-specific search
    print("3. Healthcare sector companies:")
    healthcare = stock_screener(sector="Healthcare")
    print(f"   Found {len(healthcare)} stocks:")
    if not healthcare.empty:
        for _, stock in healthcare.iterrows():
            print(f"   - {stock['Symbol']}: {stock['Company Name']} (P/E: {stock['P/E Ratio']}, ROE: {stock['ROE (%)']}%)")
    print()
    
    # Example 4: High-quality stocks
    print("4. High-quality stocks (Pillars Score >= 7):")
    high_quality = stock_screener(min_pillars_score=7)
    print(f"   Found {len(high_quality)} stocks:")
    if not high_quality.empty:
        for _, stock in high_quality.iterrows():
            print(f"   - {stock['Symbol']}: {stock['Company Name']} (Pillars Score: {stock['Pillars Score']}, Sector: {stock['Sector']})")
    print()
    
    # Example 5: Value investing criteria
    print("5. Value investing criteria (P/E <= 20, Price/Book <= 10, ROE >= 15%):")
    value_stocks = stock_screener(pe_ratio_max=20, price_book_max=10, roe_min=15)
    print(f"   Found {len(value_stocks)} stocks:")
    if not value_stocks.empty:
        for _, stock in value_stocks.iterrows():
            print(f"   - {stock['Symbol']}: {stock['Company Name']} (P/E: {stock['P/E Ratio']}, P/B: {stock['Price/Book']}, ROE: {stock['ROE (%)']}%)")
    else:
        print("   No stocks found matching these criteria")

if __name__ == "__main__":
    main()