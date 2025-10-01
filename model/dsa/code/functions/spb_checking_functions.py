"""
SPB Path Checking Functions

This module provides utility functions for checking Structural Primary Balance (SPB) paths
against European Commission Debt Sustainability Analysis (DSA) criteria.

Author: Based on EU_DSA codebase by Lennard Welslau
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Union, Optional


def check_spb_against_all_criteria(country: str, 
                                 spb_path: Union[List[float], np.ndarray], 
                                 check_deterministic: bool = True,
                                 check_stochastic: bool = True,
                                 scenarios: Optional[List[str]] = None,
                                 prob_target: Optional[float] = None,
                                 **model_kwargs) -> Dict:
    """
    Check whether a given SPB path meets all DSA criteria (deterministic and stochastic).
    
    Parameters:
    -----------
    country : str
        ISO country code (e.g., 'DEU', 'FRA', 'ITA')
    spb_path : array-like
        SPB path as percentage of GDP. Should cover the adjustment period.
    check_deterministic : bool
        Whether to check deterministic criteria (default: True)
    check_stochastic : bool
        Whether to check stochastic criteria (default: True)
    scenarios : list of str, optional
        Specific deterministic scenarios to check. If None, checks all scenarios.
    prob_target : float, optional
        Target probability for stochastic criteria. If None, uses default (0.7).
    **model_kwargs
        Additional arguments passed to model initialization
        
    Returns:
    --------
    dict
        Dictionary containing comprehensive results for all criteria checked
    """
    # Import here to avoid circular imports
    from ..classes.StochasticDsaModelClass import StochasticDsaModel
    
    # Convert input to numpy array
    spb_path = np.array(spb_path)
    
    # Initialize the stochastic DSA model (includes deterministic capabilities)
    model = StochasticDsaModel(country=country, **model_kwargs)
    
    results = {
        'country': country,
        'spb_path': spb_path.tolist(),
        'adjustment_period': model.adjustment_period,
        'adjustment_start_year': model.adjustment_start_year
    }
    
    # Check deterministic criteria
    if check_deterministic:
        try:
            deterministic_results = model.check_spb_path(spb_path, scenarios=scenarios)
            results['deterministic'] = deterministic_results['deterministic']
        except Exception as e:
            results['deterministic'] = {'error': str(e)}
    
    # Check stochastic criteria
    if check_stochastic:
        try:
            stochastic_results = model.check_spb_path_stochastic(spb_path, prob_target=prob_target)
            # Remove duplicate keys that are already in results
            for key in ['country', 'spb_path', 'adjustment_period', 'adjustment_start_year']:
                stochastic_results.pop(key, None)
            results.update(stochastic_results)
        except Exception as e:
            results['stochastic'] = {'error': str(e)}
    
    return results


def check_multiple_spb_paths(countries: List[str], 
                            spb_paths: Dict[str, Union[List[float], np.ndarray]],
                            check_deterministic: bool = True,
                            check_stochastic: bool = True,
                            scenarios: Optional[List[str]] = None,
                            prob_target: Optional[float] = None,
                            **model_kwargs) -> Dict:
    """
    Check SPB paths for multiple countries.
    
    Parameters:
    -----------
    countries : list of str
        List of country ISO codes
    spb_paths : dict
        Dictionary mapping country codes to SPB paths
    check_deterministic : bool
        Whether to check deterministic criteria (default: True)
    check_stochastic : bool
        Whether to check stochastic criteria (default: True)
    scenarios : list of str, optional
        Specific deterministic scenarios to check
    prob_target : float, optional
        Target probability for stochastic criteria
    **model_kwargs
        Additional arguments passed to model initialization
        
    Returns:
    --------
    dict
        Dictionary containing results for all countries
    """
    results = {}
    
    for country in countries:
        if country not in spb_paths:
            print(f"Warning: No SPB path provided for {country}")
            continue
            
        try:
            results[country] = check_spb_against_all_criteria(
                country=country,
                spb_path=spb_paths[country],
                check_deterministic=check_deterministic,
                check_stochastic=check_stochastic,
                scenarios=scenarios,
                prob_target=prob_target,
                **model_kwargs
            )
        except Exception as e:
            results[country] = {'error': str(e)}
    
    return results


def summarize_spb_results(results: Dict) -> pd.DataFrame:
    """
    Create a summary table of SPB path checking results.
    
    Parameters:
    -----------
    results : dict
        Results from check_spb_against_all_criteria or check_multiple_spb_paths
        
    Returns:
    --------
    pd.DataFrame
        Summary table of results
    """
    summary_data = []
    
    for country, country_results in results.items():
        if 'error' in country_results:
            summary_data.append({
                'Country': country,
                'Error': country_results['error'],
                'Deterministic_Met': False,
                'Stochastic_Met': False,
                'Overall_Met': False
            })
            continue
        
        # Check deterministic criteria
        deterministic_met = True
        if 'deterministic' in country_results:
            for scenario, scenario_results in country_results['deterministic'].items():
                if not scenario_results.get('criterion_met', False):
                    deterministic_met = False
                    break
        
        # Check stochastic criteria
        stochastic_met = False
        if 'overall' in country_results:
            stochastic_met = country_results['overall'].get('criterion_met', False)
        
        summary_data.append({
            'Country': country,
            'Deterministic_Met': deterministic_met,
            'Stochastic_Met': stochastic_met,
            'Overall_Met': deterministic_met and stochastic_met,
            'SPB_Target': country_results.get('spb_path', [None])[-1],
            'Debt_Declines_Prob': country_results.get('debt_declines', {}).get('probability', None),
            'Debt_Below_60_Prob': country_results.get('debt_below_60', {}).get('probability', None)
        })
    
    return pd.DataFrame(summary_data)