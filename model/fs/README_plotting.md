# Plotting Functions for DZ Fiscal Sustainability Model

This module provides flexible plotting capabilities for fiscal sustainability model results, allowing users to create various types of visualizations and comparisons between baseline and scenario results.

## Features

- **Flexible Variable Selection**: Plot any number of variables with automatic layout optimization
- **Multiple Plot Types**: Compare baseline vs. scenario, show differences, or display individual results
- **Customizable Time Ranges**: Specify any year range for analysis
- **Professional Styling**: Clean, publication-ready plots with proper labels and legends
- **Export Capabilities**: Save plots as high-resolution images
- **Summary Tables**: Generate comparison tables for selected variables and years

## Main Function: `plot_model_results`

### Basic Usage

```python
from plotting_functions import plot_model_results

# Basic comparison plot
fig = plot_model_results(
    baseline=baseline_data,
    scenario=scenario_data,
    variables=['G_Y_D', 'D_RATIO'],
    years=(2025, 2045),
    plot_type='comparison'
)
plt.show()
```

### Parameters

- **`baseline`**: DataFrame with baseline scenario data (years as index, variables as columns)
- **`scenario`**: DataFrame with alternative scenario data
- **`variables`**: List of variable names to plot
- **`years`**: Tuple of (start_year, end_year) for time range
- **`plot_type`**: Type of visualization:
  - `'comparison'`: Show both baseline and scenario (default)
  - `'baseline'`: Show only baseline results
  - `'scenario'`: Show only scenario results
  - `'difference'`: Show absolute difference (scenario - baseline)
  - `'percent_diff'`: Show percentage difference
- **`figsize`**: Figure size as (width, height) tuple
- **`save_path`**: Optional path to save the figure

### Layout Behavior

- **Single Variable**: Uses full width of the figure
- **Multiple Variables**: Arranges in rows of 2 variables side by side
- **Automatic Sizing**: Optimizes figure dimensions based on number of variables

## Available Variables

The module includes comprehensive variable descriptions for all major model components:

### Supply Block
- `G_Y_STAR`: Potential Output Growth (%)
- `Y_STAR`: Potential Output (Real)
- `K_M`: Private Capital Stock
- `K_G`: Public Capital Stock
- `L_TREND`: Trend Labor Input
- `U_TREND`: Trend Unemployment Rate (NAWRU)

### Demand Block
- `G_Y_D`: Real GDP Growth (%)
- `Y_D`: Real GDP (Demand-side)
- `Y_GAP`: Output Gap (%)

### Fiscal Block
- `PB_RATIO`: Primary Balance (% of GDP)
- `D_RATIO`: Debt-to-GDP Ratio (%)
- `T_HH`: Household Taxes
- `I_G`: Government Investment
- `S_IG_STAR`: Structural Government Investment Share (% of GDP)

### Financial Block
- `I_LT`: Long-term Interest Rate (%)
- `R_LT`: Real Long-term Interest Rate (%)
- `INTSHARE`: Interest Share (% of GDP)

## Plot Types Examples

### 1. Comparison Plot
```python
fig = plot_model_results(
    baseline, scenario, 
    ['G_Y_D', 'D_RATIO'], 
    plot_type='comparison'
)
```

### 2. Difference Analysis
```python
fig = plot_model_results(
    baseline, scenario, 
    ['D_RATIO', 'PB_RATIO'], 
    plot_type='difference'
)
```

### 3. Percentage Difference
```python
fig = plot_model_results(
    baseline, scenario, 
    ['G_Y_D'], 
    plot_type='percent_diff'
)
```

### 4. Single Scenario
```python
fig = plot_model_results(
    baseline, scenario, 
    ['G_Y_D', 'G_Y_STAR'], 
    plot_type='baseline'
)
```

## Convenience Functions

### Growth Comparison
```python
from plotting_functions import plot_growth_comparison

fig = plot_growth_comparison(baseline, scenario, years=(2025, 2040))
```

### Fiscal Indicators
```python
from plotting_functions import plot_fiscal_indicators

fig = plot_fiscal_indicators(baseline, scenario, years=(2025, 2045))
```

### Debt Analysis
```python
from plotting_functions import plot_debt_analysis

fig = plot_debt_analysis(baseline, scenario, years=(2025, 2045))
```

### Investment Analysis
```python
from plotting_functions import plot_investment_analysis

fig = plot_investment_analysis(baseline, scenario, years=(2025, 2045))
```

## Summary Tables

Generate comparison tables for analysis:

```python
from plotting_functions import create_summary_table

summary = create_summary_table(
    baseline, scenario,
    variables=['G_Y_D', 'D_RATIO', 'PB_RATIO'],
    years=[2025, 2030, 2035, 2040, 2045],
    plot_type='comparison'
)
print(summary)
```

## Data Format Requirements

Your DataFrames should have:
- **Index**: Years (integers)
- **Columns**: Variable names matching those in `VARIABLE_DESCRIPTIONS`
- **Values**: Numeric data for each variable-year combination

Example:
```python
# Sample data structure
baseline_data = pd.DataFrame({
    'G_Y_D': [2.5, 2.3, 2.1, ...],
    'D_RATIO': [65.0, 64.5, 64.0, ...],
    'PB_RATIO': [-1.0, -0.8, -0.6, ...]
}, index=[2025, 2026, 2027, ...])
```

## Customization

### Figure Size
```python
fig = plot_model_results(
    baseline, scenario, 
    ['G_Y_D', 'D_RATIO'], 
    figsize=(16, 10)
)
```

### Save to File
```python
fig = plot_model_results(
    baseline, scenario, 
    ['G_Y_D', 'D_RATIO'], 
    save_path='my_plot.png'
)
```

## Error Handling

The function includes validation for:
- Empty variable lists
- Invalid plot types
- Invalid year ranges
- Missing data

## Dependencies

- `matplotlib` >= 3.0
- `pandas` >= 1.0
- `numpy` >= 1.18

## Example Workflow

```python
# 1. Load your data
baseline = load_baseline_data()
scenario = load_scenario_data()

# 2. Create comparison plots
fig1 = plot_model_results(
    baseline, scenario, 
    ['G_Y_D', 'D_RATIO'], 
    years=(2025, 2040)
)

# 3. Analyze differences
fig2 = plot_model_results(
    baseline, scenario, 
    ['PB_RATIO'], 
    plot_type='difference'
)

# 4. Generate summary
summary = create_summary_table(
    baseline, scenario,
    ['G_Y_D', 'D_RATIO', 'PB_RATIO'],
    [2025, 2030, 2035, 2040]
)

# 5. Save results
fig1.savefig('growth_debt_comparison.png', dpi=300, bbox_inches='tight')
summary.to_csv('summary_results.csv', index=False)
```

## Tips for Best Results

1. **Variable Selection**: Choose related variables for meaningful comparisons
2. **Time Range**: Select appropriate time horizons for your analysis
3. **Plot Type**: Use 'difference' or 'percent_diff' for impact analysis
4. **Figure Size**: Adjust `figsize` for presentation or publication needs
5. **Export**: Use high DPI (300+) for publication-quality images
