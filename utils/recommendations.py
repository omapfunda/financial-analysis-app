"""
Investment recommendation utilities
"""


class ValuationRecommendation:
    """Class to hold valuation recommendation data in the format expected by templates"""
    def __init__(self, title, class_name, message):
        self.title = title
        setattr(self, 'class', class_name)  # Use setattr since 'class' is a reserved keyword
        self.message = message


def get_valuation_recommendation(current_price, intrinsic_value):
    """
    Get valuation recommendation based on current price vs intrinsic value
    """
    if current_price is None or intrinsic_value is None or intrinsic_value <= 0:
        return ValuationRecommendation(
            title='Insufficient Data',
            class_name='alert-secondary',
            message='Unable to determine valuation due to insufficient data'
        )
    
    ratio = current_price / intrinsic_value
    
    if ratio <= 0.7:  # Stock is trading at 70% or less of intrinsic value
        return ValuationRecommendation(
            title='Strong Buy',
            class_name='alert-success',
            message=f'Stock appears significantly undervalued (trading at {ratio:.1%} of intrinsic value)'
        )
    elif ratio <= 0.9:  # Stock is trading at 70-90% of intrinsic value
        return ValuationRecommendation(
            title='Buy',
            class_name='alert-success',
            message=f'Stock appears undervalued (trading at {ratio:.1%} of intrinsic value)'
        )
    elif ratio <= 1.1:  # Stock is trading at 90-110% of intrinsic value
        return ValuationRecommendation(
            title='Hold',
            class_name='alert-warning',
            message=f'Stock appears fairly valued (trading at {ratio:.1%} of intrinsic value)'
        )
    else:  # Stock is trading at more than 110% of intrinsic value
        return ValuationRecommendation(
            title='Sell',
            class_name='alert-danger',
            message=f'Stock appears overvalued (trading at {ratio:.1%} of intrinsic value)'
        )


def get_risk_recommendation(risk_metrics):
    """
    Get risk-based recommendation based on portfolio risk metrics
    """
    if not risk_metrics:
        return {
            'recommendation': 'Insufficient Data',
            'color': 'secondary',
            'icon': 'question-circle',
            'description': 'Unable to assess risk due to insufficient data'
        }
    
    volatility = risk_metrics.get('volatility', 0)
    sharpe_ratio = risk_metrics.get('sharpe_ratio', 0)
    max_drawdown = risk_metrics.get('max_drawdown', 0)
    
    # Risk scoring based on multiple factors
    risk_score = 0
    
    # Volatility assessment (lower is better)
    if volatility < 0.15:  # Low volatility
        risk_score += 1
    elif volatility > 0.30:  # High volatility
        risk_score -= 1
    
    # Sharpe ratio assessment (higher is better)
    if sharpe_ratio > 1.0:  # Good risk-adjusted returns
        risk_score += 1
    elif sharpe_ratio < 0.5:  # Poor risk-adjusted returns
        risk_score -= 1
    
    # Max drawdown assessment (lower absolute value is better)
    if abs(max_drawdown) < 0.10:  # Low drawdown
        risk_score += 1
    elif abs(max_drawdown) > 0.25:  # High drawdown
        risk_score -= 1
    
    # Generate recommendation based on risk score
    if risk_score >= 2:
        return {
            'recommendation': 'Low Risk',
            'color': 'success',
            'icon': 'shield-check',
            'description': 'Portfolio shows good risk characteristics with stable returns'
        }
    elif risk_score >= 0:
        return {
            'recommendation': 'Moderate Risk',
            'color': 'warning',
            'icon': 'shield',
            'description': 'Portfolio has balanced risk profile with acceptable volatility'
        }
    else:
        return {
            'recommendation': 'High Risk',
            'color': 'danger',
            'icon': 'shield-exclamation',
            'description': 'Portfolio shows elevated risk characteristics requiring attention'
        }