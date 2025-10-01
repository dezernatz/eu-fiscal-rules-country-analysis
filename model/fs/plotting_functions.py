"""
Plotting functions for the DZ Fiscal Sustainability Model.

This module provides flexible plotting capabilities for model results, including
baseline vs. scenario comparisons and difference analysis.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.ticker import MaxNLocator
from typing import List, Union, Optional, Tuple

# Variable descriptions for better legends
VARIABLE_DESCRIPTIONS = {
    # Supply block variables
    'G_Y_STAR': 'Potential Output Growth (%)',
    'Y_STAR': 'Potential Output (Real)',
    'Y_STAR_NOM': 'Potential Output (Nominal)',
    'SR_TREND': 'Total Factor Productivity (Log)',
    'K_M': 'Private Capital Stock',
    'K_G': 'Public Capital Stock',
    'K_M_LOG': 'Private Capital Stock (Log)',
    'K_G_LOG': 'Public Capital Stock (Log)',
    'L_TREND': 'Trend Labor Input',
    'L_TREND_LOG': 'Trend Labor Input (Log)',
    'LP_TREND': 'Trend Participation Rate',
    'U_TREND': 'Trend Unemployment Rate (NAWRU)',
    'H_TREND': 'Trend Average Hours Worked',
    
    # Demand block variables
    'G_Y_D': 'Real GDP Growth (%)',
    'Y_D': 'Real GDP (Demand-side)',
    'Y_D_LOG': 'Real GDP (Log)',
    'Y_D_NOM': 'Nominal GDP (Demand-side)',
    'Y_GAP': 'Output Gap (%)',
    
    # Fiscal block variables
    'PB': 'Primary Balance',
    'PB_RATIO': 'Primary Balance (% of GDP)',
    'GR': 'Government Revenue',
    'PE': 'Primary Expenditure',
    'T_HH': 'Household Taxes',
    'T_F': 'Corporate Taxes',
    'T_C': 'Consumption Taxes',
    'SC_HH': 'Household Social Contributions',
    'SC_F': 'Corporate Social Contributions',
    'SC_IMP': 'Imputed Social Contributions',
    'NON_T': 'Non-Tax Revenue',
    'G': 'Government Consumption',
    'I_G': 'Government Investment',
    'SUB': 'Government Subsidies',
    'TR': 'Government Transfers',
    'OTHER_PE': 'Other Primary Expenditure',
    
    # Debt dynamics
    'D_RATIO': 'Debt-to-GDP Ratio (%)',
    'D': 'Nominal Government Debt',
    'GFN': 'Gross Financing Needs',
    'INT': 'Interest Payments',
    'INTSHARE': 'Interest Share (% of GDP)',
    'REP': 'Debt Repayments',
    'SF': 'Stock-Flow Adjustment',
    'IIR': 'Implicit Interest Rate (%)',
    'IIR_LT': 'Long-term Implicit Interest Rate (%)',
    
    # Financial block
    'I_RATE': 'Policy Interest Rate (%)',
    'I_ST': 'Short-term Interest Rate (%)',
    'I_LT': 'Long-term Interest Rate (%)',
    'R_ST': 'Real Short-term Interest Rate (%)',
    'R_LT': 'Real Long-term Interest Rate (%)',
    'TERM': 'Term Premium (%)',
    'RISK': 'Fiscal Risk Premium (%)',
    
    # Price variables
    'PI': 'Inflation Rate (%)',
    'P': 'Price Level',
    'G_Y_STAR_NOM': 'Nominal Potential Output Growth (%)',
    'G_Y_D_NOM': 'Nominal GDP Growth (%)',
    
    # Investment variables
    'IQ_M': 'Private Investment Rate (%)',
    'S_IG': 'Government Investment Share (% of GDP)',
    'S_IG_STAR': 'Structural Government Investment Share (% of GDP)',
    
    # Real values
    'T_HH_REAL': 'Real Household Taxes',
    'T_F_REAL': 'Real Corporate Taxes',
    'T_C_REAL': 'Real Consumption Taxes',
    'G_REAL': 'Real Government Consumption',
    'I_G_REAL': 'Real Government Investment',
    'SUB_REAL': 'Real Government Subsidies',
    'TR_REAL': 'Real Government Transfers'
}

def plot_model_results(
    baseline: pd.DataFrame,
    scenario: pd.DataFrame,
    variables: List[str],
    years: Tuple[int, int] = (2025, 2045),
    plot_type: str = 'comparison',
    figsize: Tuple[int, int] = (20, 5),
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot fiscal sustainability model results with flexible options.
    
    Parameters:
    -----------
    baseline : pd.DataFrame
        Baseline scenario data with variables as columns and years as index
    scenario : pd.DataFrame
        Alternative scenario data with variables as columns and years as index
    variables : List[str]
        List of variable names to plot
    years : Tuple[int, int], optional
        Year range to display (start_year, end_year), default (2025, 2045)
    plot_type : str, optional
        Type of plot: 'baseline', 'scenario', 'comparison', 'difference', 'percent_diff'
        - 'baseline': Show only baseline results
        - 'scenario': Show only scenario results  
        - 'comparison': Show both baseline and scenario
        - 'difference': Show absolute difference (scenario - baseline)
        - 'percent_diff': Show percentage difference ((scenario - baseline) / baseline * 100)
    figsize : Tuple[int, int], optional
        Figure size (width, height), default (22, 14)
    save_path : str, optional
        Path to save the figure, if None figure is not saved
        
    Returns:
    --------
    plt.Figure
        The created matplotlib figure
        
    Examples:
    ---------
    # Compare GDP growth and debt ratio
    fig = plot_model_results(baseline, scenario, ['G_Y_D', 'D_RATIO'], 
                           plot_type='comparison')
    
    # Show only baseline results for multiple variables
    fig = plot_model_results(baseline, scenario, ['G_Y_D', 'G_Y_STAR', 'PB_RATIO'], 
                           plot_type='baseline')
    
    # Show percentage differences
    fig = plot_model_results(baseline, scenario, ['D_RATIO'], 
                           plot_type='percent_diff')
    """
    
    # Validate inputs
    if not isinstance(variables, list) or len(variables) == 0:
        raise ValueError("variables must be a non-empty list")
    
    if plot_type not in ['baseline', 'scenario', 'comparison', 'difference', 'percent_diff']:
        raise ValueError("plot_type must be one of: 'baseline', 'scenario', 'comparison', 'difference', 'percent_diff'")
    
    start_year, end_year = years
    if start_year >= end_year:
        raise ValueError("start_year must be less than end_year")
    
    # Filter data for specified years
    baseline_filtered = baseline.loc[start_year:end_year]
    scenario_filtered = scenario.loc[start_year:end_year]
    
    # Determine subplot layout
    n_vars = len(variables)
    if n_vars == 1:
        # Single variable: use full width
        n_cols = 1
        n_rows = 1
        figsize = (figsize[0], figsize[1] // 2)  # Reduce height for single plot
    else:
        # Multiple variables: arrange in rows of 2
        n_cols = 2
        n_rows = (n_vars + 1) // 2  # Ceiling division
    
    # Create figure and subplots
    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    
    # Handle single subplot case
    if n_vars == 1:
        axes = [axes]
    elif n_rows == 1:
        axes = [axes] if n_cols == 1 else axes
    else:
        axes = axes.flatten()
    
    # Plot each variable
    for i, var in enumerate(variables):
        if i >= len(axes):
            break
            
        ax = axes[i]
        
        # Get variable description for title and labels
        var_desc = VARIABLE_DESCRIPTIONS.get(var, var)
        
        # Determine y-axis label based on variable
        if 'RATIO' in var or 'GAP' in var or 'SHARE' in var or var in ['U_TREND', 'LP_TREND']:
            ylabel = f"{var_desc} (%)"
        elif 'GROWTH' in var_desc.upper() or 'G_Y' in var:
            ylabel = f"{var_desc} (%)"
        elif 'RATE' in var_desc.upper() or var in ['PI', 'IIR', 'I_RATE', 'I_ST', 'I_LT', 'R_ST', 'R_LT']:
            ylabel = f"{var_desc} (%)"
        else:
            ylabel = var_desc
        
        # Plot based on plot type
        if plot_type == 'baseline':
            ax.plot(baseline_filtered.index, baseline_filtered[var],
                   label='Baseline', linewidth=3, color='blue')
            title = f"{var_desc} - Baseline"
            
        elif plot_type == 'scenario':
            ax.plot(scenario_filtered.index, scenario_filtered[var],
                   label='Scenario', linewidth=3, color='red')
            title = f"{var_desc} - Scenario"
            
        elif plot_type == 'comparison':
            ax.plot(baseline_filtered.index, baseline_filtered[var],
                   label='Baseline', linewidth=3, color='blue')
            ax.plot(scenario_filtered.index, scenario_filtered[var],
                   label='Scenario', linewidth=3, color='red', linestyle='--')
            title = f"{var_desc} - Comparison"
            
        elif plot_type == 'difference':
            diff = scenario_filtered[var] - baseline_filtered[var]
            ax.plot(baseline_filtered.index, diff,
                   label='Difference (Scenario - Baseline)', linewidth=3, color='green')
            title = f"{var_desc} - Absolute Difference"
            
        elif plot_type == 'percent_diff':
            # Avoid division by zero
            baseline_values = baseline_filtered[var]
            percent_diff = np.where(baseline_values != 0, 
                                  (scenario_filtered[var] - baseline_values) / baseline_values * 100, 
                                  0)
            ax.plot(baseline_filtered.index, percent_diff,
                   label='Percentage Difference', linewidth=3, color='purple')
            title = f"{var_desc} - Percentage Difference (%)"
        
        # Customize subplot
        ax.set_xlabel('Year', fontsize=14)
        ax.set_ylabel(ylabel, fontsize=14)
        ax.set_title(title, fontsize=16)
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', labelsize=12)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        
        # Add horizontal line at zero for difference plots
        if plot_type in ['difference', 'percent_diff']:
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    
    # Hide unused subplots
    for i in range(n_vars, len(axes)):
        axes[i].set_visible(False)
    
    plt.tight_layout()
    
    # Save figure if path is provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig

def create_summary_table(
    baseline: pd.DataFrame,
    scenario: pd.DataFrame,
    variables: List[str],
    years: List[int],
    plot_type: str = 'comparison'
) -> pd.DataFrame:
    """
    Create a summary table comparing baseline and scenario results.
    
    Parameters:
    -----------
    baseline : pd.DataFrame
        Baseline scenario data
    scenario : pd.DataFrame
        Alternative scenario data
    variables : List[str]
        List of variable names to include
    years : List[int]
        List of years to include in summary
    plot_type : str
        Type of comparison to show
        
    Returns:
    --------
    pd.DataFrame
        Summary table with comparisons
    """
    
    summary_data = []
    
    for var in variables:
        var_desc = VARIABLE_DESCRIPTIONS.get(var, var)
        
        for year in years:
            if year in baseline.index and year in scenario.index:
                baseline_val = baseline.loc[year, var]
                scenario_val = scenario.loc[year, var]
                
                if plot_type == 'difference':
                    diff = scenario_val - baseline_val
                    summary_data.append({
                        'Variable': var_desc,
                        'Year': year,
                        'Baseline': baseline_val,
                        'Scenario': scenario_val,
                        'Difference': diff
                    })
                elif plot_type == 'percent_diff':
                    if baseline_val != 0:
                        percent_diff = (scenario_val - baseline_val) / baseline_val * 100
                    else:
                        percent_diff = 0
                    summary_data.append({
                        'Variable': var_desc,
                        'Year': year,
                        'Baseline': baseline_val,
                        'Scenario': scenario_val,
                        'Percent Difference (%)': percent_diff
                    })
                else:
                    summary_data.append({
                        'Variable': var_desc,
                        'Year': year,
                        'Baseline': baseline_val,
                        'Scenario': scenario_val
                    })
    
    return pd.DataFrame(summary_data)

# Convenience functions for common plotting tasks
def plot_growth_comparison(baseline: pd.DataFrame, scenario: pd.DataFrame, 
                          years: Tuple[int, int] = (2025, 2045)) -> plt.Figure:
    """Plot GDP and potential output growth comparison."""
    return plot_model_results(baseline, scenario, ['G_Y_D', 'G_Y_STAR'], 
                            years, 'comparison')

def plot_fiscal_indicators(baseline: pd.DataFrame, scenario: pd.DataFrame,
                          years: Tuple[int, int] = (2025, 2045)) -> plt.Figure:
    """Plot key fiscal indicators comparison."""
    return plot_model_results(baseline, scenario, ['PB_RATIO', 'D_RATIO'], 
                            years, 'comparison')

def plot_debt_analysis(baseline: pd.DataFrame, scenario: pd.DataFrame,
                      years: Tuple[int, int] = (2025, 2045)) -> plt.Figure:
    """Plot debt-related variables comparison."""
    return plot_model_results(baseline, scenario, ['D_RATIO', 'INTSHARE', 'GFN'], 
                            years, 'comparison')

def plot_investment_analysis(baseline: pd.DataFrame, scenario: pd.DataFrame,
                           years: Tuple[int, int] = (2025, 2045)) -> plt.Figure:
    """Plot investment-related variables comparison."""
    return plot_model_results(baseline, scenario, ['S_IG_STAR', 'IQ_M', 'K_G'], 
                            years, 'comparison')
