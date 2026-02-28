"""
Savings Engine - Financial calculations and visualizations
"""

import pandas as pd
import plotly.graph_objects as go


class SavingsEngine:
    """Handle savings calculations and generate financial charts"""
    
    @staticmethod
    def calculate_compound_interest(principal: float, rate: float, years: int, frequency: int = 12) -> dict:
        """
        Calculate compound interest growth
        
        Args:
            principal: Initial investment amount
            rate: Annual interest rate (as percentage, e.g., 8 for 8%)
            years: Investment period in years
            frequency: Compounding frequency per year (12 for monthly)
            
        Returns:
            Dictionary with calculation results
        """
        rate_decimal = rate / 100
        amount = principal * (1 + rate_decimal / frequency) ** (frequency * years)
        interest_earned = amount - principal
        
        return {
            "principal": principal,
            "rate": rate,
            "years": years,
            "final_amount": round(amount, 2),
            "interest_earned": round(interest_earned, 2),
            "total_return": round((interest_earned / principal) * 100, 2)
        }
    
    @staticmethod
    def generate_growth_chart(principal: float = 10000, rate: float = 8, max_years: int = 30):
        """
        Generate interactive Plotly chart showing savings growth
        
        Args:
            principal: Initial investment
            rate: Annual interest rate
            max_years: Maximum years to project
            
        Returns:
            Plotly figure object
        """
        years = list(range(0, max_years + 1))
        
        # Calculate simple and compound interest
        simple_interest = [principal + (principal * rate / 100 * year) for year in years]
        compound_interest = [principal * (1 + rate / 100) ** year for year in years]
        
        # Create DataFrame
        df = pd.DataFrame({
            'Years': years,
            'Simple Interest': simple_interest,
            'Compound Interest': compound_interest
        })
        
        # Create Plotly figure
        fig = go.Figure()
        
        # Add Simple Interest line
        fig.add_trace(go.Scatter(
            x=df['Years'],
            y=df['Simple Interest'],
            mode='lines',
            name='Simple Interest',
            line=dict(color='#94A3B8', width=2, dash='dash'),
            hovertemplate='<b>Year %{x}</b><br>Amount: ₹%{y:,.0f}<extra></extra>'
        ))
        
        # Add Compound Interest line
        fig.add_trace(go.Scatter(
            x=df['Years'],
            y=df['Compound Interest'],
            mode='lines',
            name='Compound Interest',
            line=dict(color='#3B82F6', width=3),
            fill='tonexty',
            fillcolor='rgba(59, 130, 246, 0.1)',
            hovertemplate='<b>Year %{x}</b><br>Amount: ₹%{y:,.0f}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title=f'Investment Growth: ₹{principal:,} at {rate}% Annual Return',
            xaxis_title='Years',
            yaxis_title='Amount (₹)',
            hovermode='x unified',
            template='plotly_white',
            font=dict(family='Inter, sans-serif', size=12),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=400,
            margin=dict(l=60, r=40, t=80, b=60)
        )
        
        return fig
    
    @staticmethod
    def generate_comparison_data(principal: float, years: int) -> pd.DataFrame:
        """
        Generate comparison data for different investment options
        
        Args:
            principal: Initial investment amount
            years: Investment period
            
        Returns:
            DataFrame with comparison data
        """
        options = {
            'Savings Account': 3.5,
            'Fixed Deposit': 6.5,
            'PPF': 7.1,
            'Mutual Funds': 12,
            'Equity (Long-term)': 15
        }
        
        results = []
        for option, rate in options.items():
            final_amount = principal * (1 + rate / 100) ** years
            results.append({
                'Investment Option': option,
                'Interest Rate': f'{rate}%',
                'Final Amount': f'₹{final_amount:,.0f}',
                'Returns': f'₹{final_amount - principal:,.0f}'
            })
        
        return pd.DataFrame(results)
    
    @staticmethod
    def sip_calculator(monthly_investment: float, rate: float, years: int) -> dict:
        """
        Calculate SIP (Systematic Investment Plan) returns
        
        Args:
            monthly_investment: Monthly SIP amount
            rate: Expected annual return rate
            years: Investment period
            
        Returns:
            Dictionary with SIP calculation results
        """
        months = years * 12
        monthly_rate = rate / 12 / 100
        
        # Future value of SIP
        if monthly_rate == 0:
            fv = monthly_investment * months
        else:
            fv = monthly_investment * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
        
        total_invested = monthly_investment * months
        returns = fv - total_invested
        
        return {
            "monthly_investment": monthly_investment,
            "years": years,
            "total_invested": round(total_invested, 2),
            "final_value": round(fv, 2),
            "returns": round(returns, 2),
            "return_percentage": round((returns / total_invested) * 100, 2)
        }
