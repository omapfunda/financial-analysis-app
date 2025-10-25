"""
Data formatting utilities
"""
import pandas as pd


def format_financial_dataframe(df):
    """
    Format financial dataframe for better display
    """
    if df.empty:
        return df
    
    # Create a copy to avoid modifying the original
    formatted_df = df.copy()
    
    # Define rows that should not be formatted as currency (for intrinsic value tables)
    text_rows = ['Company Name', 'Sector', 'Industry']
    percentage_rows = ['Growth Rate (%)', 'Discount Rate (%)', 'Margin of Safety (%)']
    
    # Format numeric columns first (before replacing NaN values)
    for col in formatted_df.columns:
        if formatted_df[col].dtype in ['float64', 'int64', 'object']:
            # Convert to numeric, handling any non-numeric values
            numeric_col = pd.to_numeric(formatted_df[col], errors='coerce')
            
            # Format large numbers
            formatted_values = []
            for idx, val in enumerate(numeric_col):
                # Check if this row should remain as text
                row_name = formatted_df.index[idx] if idx < len(formatted_df.index) else None
                if row_name in text_rows:
                    # Keep original text value for these rows
                    original_val = formatted_df.iloc[idx, formatted_df.columns.get_loc(col)]
                    formatted_values.append(str(original_val) if not pd.isna(original_val) else 'N/A')
                elif row_name in percentage_rows:
                    # Format as percentage without dollar sign
                    if pd.isna(val):
                        formatted_values.append('N/A')
                    else:
                        formatted_values.append(f'{val:.2f}%')
                elif pd.isna(val):
                    formatted_values.append('N/A')
                elif abs(val) >= 1e9:  # Billions
                    formatted_values.append(f'${val/1e9:.2f}B')
                elif abs(val) >= 1e6:  # Millions
                    formatted_values.append(f'${val/1e6:.2f}M')
                elif abs(val) >= 1e3:  # Thousands
                    formatted_values.append(f'${val/1e3:.2f}K')
                else:
                    formatted_values.append(f'${val:.2f}')
            
            formatted_df[col] = formatted_values
    
    # Improve column names (convert years to more readable format)
    new_columns = []
    for col in formatted_df.columns:
        if isinstance(col, str) and col.isdigit() and len(col) == 4:
            new_columns.append(f'FY {col}')
        else:
            new_columns.append(str(col).replace('_', ' ').title())
    
    formatted_df.columns = new_columns
    
    return formatted_df


def format_currency(value, precision=2):
    """Format a numeric value as currency"""
    if value is None or pd.isna(value):
        return 'N/A'
    
    try:
        val = float(value)
        if abs(val) >= 1e9:  # Billions
            return f'${val/1e9:.{precision}f}B'
        elif abs(val) >= 1e6:  # Millions
            return f'${val/1e6:.{precision}f}M'
        elif abs(val) >= 1e3:  # Thousands
            return f'${val/1e3:.{precision}f}K'
        else:
            return f'${val:.{precision}f}'
    except (ValueError, TypeError):
        return 'N/A'


def format_percentage(value, precision=2):
    """Format a numeric value as percentage"""
    if value is None or pd.isna(value):
        return 'N/A'
    
    try:
        val = float(value)
        return f'{val:.{precision}f}%'
    except (ValueError, TypeError):
        return 'N/A'


def format_number(value, precision=2):
    """Format a numeric value with appropriate scaling"""
    if value is None or pd.isna(value):
        return 'N/A'
    
    try:
        val = float(value)
        if abs(val) >= 1e9:  # Billions
            return f'{val/1e9:.{precision}f}B'
        elif abs(val) >= 1e6:  # Millions
            return f'{val/1e6:.{precision}f}M'
        elif abs(val) >= 1e3:  # Thousands
            return f'{val/1e3:.{precision}f}K'
        else:
            return f'{val:.{precision}f}'
    except (ValueError, TypeError):
        return 'N/A'


def format_ratio(value, precision=2):
    """Format a ratio value"""
    if value is None or pd.isna(value):
        return 'N/A'
    
    try:
        val = float(value)
        return f'{val:.{precision}f}'
    except (ValueError, TypeError):
        return 'N/A'