#!/usr/bin/env python3
"""
Example: SPB Path Checking

This script demonstrates how to use the new SPB path checking functionality
added to the EU_DSA codebase.

The new methods allow you to check whether a given Structural Primary Balance (SPB) path
meets the European Commission's Debt Sustainability Analysis (DSA) criteria.
"""

import numpy as np
import pandas as pd
import sys
import os

# Add the code directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from classes.StochasticDsaModelClass import StochasticDsaModel
    from classes.DsaModelClass import DsaModel
    from functions.spb_checking_functions import (
        check_spb_against_all_criteria, 
        check_multiple_spb_paths, 
        summarize_spb_results
    )
    print("✓ Successfully imported SPB checking functionality")
except ImportError as e:
    print(f"✗ Failed to import: {e}")
    print("Make sure you're running this from the EU_DSA code directory")
    sys.exit(1)


def example_deterministic_only():
    """Example: Check SPB path against deterministic criteria only."""
    print("\n=== Example 1: Deterministic Criteria Only ===")
    
    # Initialize deterministic model for Germany
    model = DsaModel(country='DEU')
    
    # Define SPB path (4-year adjustment period)
    spb_path = [0.5, 1.0, 1.5, 2.0]  # Gradual increase to 2%
    
    # Check against deterministic criteria
    results = model.check_spb_path(spb_path)
    
    print(f"Country: {results['country']}")
    print(f"SPB Path: {results['spb_path']}")
    print("\nDeterministic Criteria Results:")
    
    for scenario, scenario_results in results['deterministic'].items():
        if 'error' in scenario_results:
            print(f"  {scenario}: Error - {scenario_results['error']}")
        else:
            status = "✓ PASS" if scenario_results['criterion_met'] else "✗ FAIL"
            debt_end = scenario_results['debt_end_adjustment']
            print(f"  {scenario}: {status} (Debt at end: {debt_end:.1f}%)")
    
    return results


def example_stochastic_only():
    """Example: Check SPB path against stochastic criteria only."""
    print("\n=== Example 2: Stochastic Criteria Only ===")
    
    # Initialize stochastic model for Germany
    model = StochasticDsaModel(country='DEU')
    
    # Define SPB path
    spb_path = [0.5, 1.0, 1.5, 2.0]
    
    # Check against stochastic criteria
    results = model.check_spb_path_stochastic(spb_path)
    
    print(f"Country: {results['country']}")
    print(f"SPB Path: {results['spb_path']}")
    print(f"Target Probability: {results['prob_target']:.1%}")
    print("\nStochastic Criteria Results:")
    
    if 'error' in results:
        print(f"  Error: {results['error']}")
    else:
        for criterion in ['debt_declines', 'debt_below_60']:
            if criterion in results:
                criterion_results = results[criterion]
                status = "✓ PASS" if criterion_results['criterion_met'] else "✗ FAIL"
                prob = criterion_results['probability']
                print(f"  {criterion}: {status} (Probability: {prob:.1%})")
        
        # Overall result
        if 'overall' in results:
            overall = results['overall']
            status = "✓ PASS" if overall['criterion_met'] else "✗ FAIL"
            print(f"  Overall: {status}")
    
    return results


def example_all_criteria():
    """Example: Check SPB path against all criteria using utility function."""
    print("\n=== Example 3: All Criteria (Utility Function) ===")
    
    # Define SPB path
    spb_path = [0.5, 1.0, 1.5, 2.0]
    
    # Check against all criteria
    results = check_spb_against_all_criteria(
        country='DEU',
        spb_path=spb_path,
        check_deterministic=True,
        check_stochastic=True
    )
    
    print(f"Country: {results['country']}")
    print(f"SPB Path: {results['spb_path']}")
    
    # Deterministic results
    if 'deterministic' in results:
        print("\nDeterministic Criteria:")
        for scenario, scenario_results in results['deterministic'].items():
            if 'error' in scenario_results:
                print(f"  {scenario}: Error - {scenario_results['error']}")
            else:
                status = "✓ PASS" if scenario_results['criterion_met'] else "✗ FAIL"
                print(f"  {scenario}: {status}")
    
    # Stochastic results
    if 'debt_declines' in results:
        print("\nStochastic Criteria:")
        for criterion in ['debt_declines', 'debt_below_60']:
            if criterion in results:
                criterion_results = results[criterion]
                status = "✓ PASS" if criterion_results['criterion_met'] else "✗ FAIL"
                prob = criterion_results['probability']
                print(f"  {criterion}: {status} (Probability: {prob:.1%})")
    
    return results


def example_multiple_countries():
    """Example: Check SPB paths for multiple countries."""
    print("\n=== Example 4: Multiple Countries ===")
    
    # Define SPB paths for multiple countries
    spb_paths = {
        'DEU': [0.5, 1.0, 1.5, 2.0],  # Germany: gradual increase to 2%
        'FRA': [0.0, 0.5, 1.0, 1.5],  # France: gradual increase to 1.5%
        'ITA': [-0.5, 0.0, 0.5, 1.0], # Italy: gradual increase to 1%
    }
    
    # Check all countries
    results = check_multiple_spb_paths(
        countries=['DEU', 'FRA', 'ITA'],
        spb_paths=spb_paths,
        check_deterministic=True,
        check_stochastic=True
    )
    
    # Create summary table
    summary = summarize_spb_results(results)
    print("\nSummary Table:")
    print(summary.to_string(index=False))
    
    return results, summary


def example_specific_scenarios():
    """Example: Check specific deterministic scenarios only."""
    print("\n=== Example 5: Specific Scenarios ===")
    
    # Initialize model
    model = DsaModel(country='DEU')
    
    # Define SPB path
    spb_path = [0.5, 1.0, 1.5, 2.0]
    
    # Check only specific scenarios
    specific_scenarios = ['main_adjustment', 'lower_spb', 'financial_stress']
    results = model.check_spb_path(spb_path, scenarios=specific_scenarios)
    
    print(f"Country: {results['country']}")
    print(f"SPB Path: {results['spb_path']}")
    print(f"Scenarios Checked: {specific_scenarios}")
    print("\nResults:")
    
    for scenario in specific_scenarios:
        if scenario in results['deterministic']:
            scenario_results = results['deterministic'][scenario]
            if 'error' in scenario_results:
                print(f"  {scenario}: Error - {scenario_results['error']}")
            else:
                status = "✓ PASS" if scenario_results['criterion_met'] else "✗ FAIL"
                debt_end = scenario_results['debt_end_adjustment']
                print(f"  {scenario}: {status} (Debt at end: {debt_end:.1f}%)")
    
    return results


def main():
    """Run all examples."""
    print("SPB Path Checking Examples")
    print("=" * 50)
    print("This demonstrates the new SPB path checking functionality")
    print("added to the EU_DSA codebase.")
    
    try:
        # Example 1: Deterministic only
        example_deterministic_only()
        
        # Example 2: Stochastic only
        example_stochastic_only()
        
        # Example 3: All criteria
        example_all_criteria()
        
        # Example 4: Multiple countries
        example_multiple_countries()
        
        # Example 5: Specific scenarios
        example_specific_scenarios()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("\nNew functionality added:")
        print("- DsaModel.check_spb_path(): Check deterministic criteria")
        print("- StochasticDsaModel.check_spb_path_stochastic(): Check stochastic criteria")
        print("- check_spb_against_all_criteria(): Utility function for all criteria")
        print("- check_multiple_spb_paths(): Check multiple countries")
        print("- summarize_spb_results(): Create summary tables")
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        print("This may be due to missing data files or other dependencies.")
        print("The functionality is implemented but requires the full EU_DSA data setup.")


if __name__ == "__main__":
    main()