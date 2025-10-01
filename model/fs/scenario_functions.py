"""
Scenario analysis and model initialization functions for the DZ Fiscal Sustainability Model.

CAREFUL: Convergence/anchoring is not fully implemented in the model yet.
"""

import numpy as np
from debug_utils import (
    debug_print, debug_print_section, debug_print_subsection, 
    debug_print_info, debug_print_success, debug_print_warning, debug_print_error
)

def initialize_model(
    data,
    model_class,
    start=2025,
    end=2045,
    interest_method='exogenous',
    baseline_method='EUCAM',
    LT_baseline_method='AR24',  # 'own' or 'AR24'
    beta_d_assumption='estimated',  # 'estimated' or 'zero'
    silent=1,
    max_iterations=1000000,
    invert_maxiter=1000000,
    dsa_model=None,  # Optional: pass DSA model instance for baseline_method='DSA'
    mtp_anchors=None,  # Optional: dict of Series/dicts for 'rg','pi','rg_pot' when using DSA_MTP
):
    """Initialize the model based on specifications.
    
    Parameters:
        interest_method: str, one of:
            - 'exogenous': Interest rates fully anchored to external DSA projections (RHO_I = 1)
            - 'DSA-anchored': Interest rates gradually transition from endogenous to DSA-anchored 
              using logistic function (RHO_I transitions from 0 to 1)
            - 'endogenous': Interest rates fully endogenous, responding to economic conditions (RHO_I = 0)
        baseline_method: str, either 'own' (use current model logic) or 'EUCAM' (use EUCAM targeting)
        LT_baseline_method: str, either 'own' (use current long-term logic) or 'AR24' (use AR24 long-term growth rates)
        beta_d_assumption: str, either 'estimated' (use baseline BETA_D) or 'zero' (set BETA_D=0)
                          This controls the debt sustainability coefficient and is inherited by scenarios
    """
    data_copy = data.copy()

       # Apply beta_d_assumption for ALL methods (not just EUCAM)
    if beta_d_assumption == 'zero':
        data_copy.loc[:, "BETA_D"] = 0
    # If 'estimated', keep the original BETA_D values
    
    baseline_lower = baseline_method.lower()
    # Treat 'dsa_mtp' as a synonym of 'dsa' for FS baseline setup, so existing behavior remains intact
    if baseline_lower in ('eucam', 'dsa', 'dsa_mtp'):
        # Set EUCAM trend and slope variables
        eucam_vars = ["SR_TREND", "LP_TREND", "U_TREND", "H_TREND", "SR_SLOPE", "LP_SLOPE", "U_SLOPE", "H_SLOPE"]
        for var in eucam_vars:
            data_copy.loc[:, var] = data_copy.loc[:, f"{var}_EUCAM"]
        
        # Implement EUCAM anchor: Starting 2029, hours growth rate will half each year
        # Ensure float dtype to safely assign fractional values
        for _col in ["RHO_H", "RHO_LP"]:
            if _col in data_copy.columns:
                try:
                    data_copy[_col] = data_copy[_col].astype(float)
                except Exception:
                    pass
        data_copy.loc[start + 5:end, "RHO_H"] = 0.5
        data_copy.loc[start + 5, "RHO_LP"] = 0.2
        data_copy.loc[start + 6, "RHO_LP"] = 0.4
        data_copy.loc[start + 7, "RHO_LP"] = 0.6
        data_copy.loc[start + 8, "RHO_LP"] = 0.8
        data_copy.loc[start + 9:end, "RHO_LP"] = 1
        
        set_eucam = True
    else:
        set_eucam = False

    # New: DSA baseline mode (anchors FS to DSA and enforces PB/SPB identities)
    set_dsa_baseline = baseline_lower in ('dsa', 'dsa_mtp')
    if set_dsa_baseline:
        if dsa_model is None:
            raise ValueError("baseline_method='DSA' requires a dsa_model instance")
        # If MTP anchors are provided (or baseline_method explicitly 'dsa_mtp'),
        # apply them to the DSA model BEFORE extracting anchors to FS.
        if (baseline_lower == 'dsa_mtp') or (mtp_anchors is not None):
            try:
                from integration import apply_mtp_anchors_to_dsa
                apply_mtp_anchors_to_dsa(dsa_model, anchors=(mtp_anchors or {}), inplace=True)
            except Exception as _e:
                # Do not break existing behavior if anchors application fails; log via debug utils
                debug_print_warning("DSA_MTP anchors application failed", str(_e))
        # For DSA baseline we still anchor interest/exchange/inflation and debt mechanics to DSA data
        years = np.arange(start, end + 1)
        def _arr(name):
            import numpy as _np
            idx = [y - dsa_model.start_year for y in years]
            idx = [i for i in idx if 0 <= i < dsa_model.projection_period]
            vals = getattr(dsa_model, name)[idx]
            cal_years = [dsa_model.start_year + i for i in idx]
            return cal_years, _np.array(vals, dtype=float)
        yrs, i_st = _arr('i_st')
        _, i_lt = _arr('i_lt')
        _, pi = _arr('pi')
        _, exr_usd = _arr('exr_usd')
        in_data_years = [y for y in yrs if y in data_copy.index]
        data_copy.loc[in_data_years, 'I_ST_ANCHOR'] = i_st[:len(in_data_years)]
        data_copy.loc[in_data_years, 'I_LT_ANCHOR'] = i_lt[:len(in_data_years)]
        data_copy.loc[in_data_years, 'PI'] = pi[:len(in_data_years)]
        data_copy.loc[in_data_years, 'EXR_USD'] = exr_usd[:len(in_data_years)]
        # Debt mechanics
        _, d_share_lt_maturing = _arr('D_share_lt_maturing')
        _, sf_ratio = _arr('sf')
        data_copy.loc[in_data_years, 'PHI_LT'] = d_share_lt_maturing[:len(in_data_years)]
        data_copy.loc[in_data_years, 'SF_RATIO'] = sf_ratio[:len(in_data_years)]
        #D_share_usd = float(getattr(dsa_model, 'D_share_usd', 0.0))
        #data_copy.loc[in_data_years, 'ALPHA_USD'] = D_share_usd
        #data_copy.loc[in_data_years, 'ALPHA_EUR'] = 1 - D_share_usd

    # Handle interest rate method
    # RHO_I controls the degree of DSA anchoring:
    # - RHO_I = 1: Fully anchored to external DSA projections
    # - RHO_I = 0: Fully endogenous, responding to economic conditions
    # - 0 < RHO_I < 1: Partial anchoring (logistic transition)
    # Align FS start so that start-1 exists (DSA typically anchors T=start-1)
    # If FS data does not contain start-1, shift the FS solving window by one year earlier if available
    years = np.arange(start - 1, end + 1)
    years_in_data = [year for year in years if year in data_copy.index]
    
    if interest_method == 'exogenous':
        data_copy.loc[years_in_data, "RHO_I"] = 1
    elif interest_method == 'DSA-anchored':
        data_copy.loc[years_in_data, "RHO_I"] = data_copy.loc[years_in_data, "RHO_I_VALUES"]
    elif interest_method == 'endogenous':
        data_copy.loc[years_in_data, "RHO_I"] = 0

    # Apply fix pattern with different time periods for slopes
    # First fix SR_SLOPE until 2025
    result = model_class.fix(data_copy, pat="SR_SLOPE", start=start, end=2025, silent=silent)
    
    # Then fix other slopes until 2028
    if set_eucam == True:
        result = model_class.fix(result, pat="LP_SLOPE H_SLOPE", start=start, end=2028, silent=silent)
        result = model_class.fix(result, pat="U_TREND", start=start, end=end, silent=silent)
    else:
        result = model_class.fix(result, pat="LP_SLOPE U_SLOPE H_SLOPE", start=start, end=2028, silent=silent)
    
    # Solve the model (initial pass)
    result = model_class(
        result, start, end, max_iterations=max_iterations, init=True, silent=silent, reset_options=True
    )

    # If DSA baseline: apply EUCAM-style sequential targeting but with growth-rate targets
    if set_dsa_baseline:
        result = apply_targets_sequentially_baseline_dsa(
            result, data_copy, model_class, invert_maxiter, start, end, dsa_model
        )

    # Solve the model with EUCAM targets
    # Apply EUCAM sequential targets in 'EUCAM' mode; in 'DSA' mode we already applied the DSA variant
    if set_eucam and not set_dsa_baseline:
        result = apply_targets_sequentially_baseline(
            result, data_copy, model_class, invert_maxiter, start, end, LT_baseline_method
        )
    # Note: DSA baseline does not use LT_baseline_method targeting by design

    # Store baseline options for scenario inheritance
    # These options will be automatically used by run_scenario_analysis
    model_class.baseline_options = {
        'baseline_method': baseline_method,
        'LT_baseline_method': (None if set_dsa_baseline else LT_baseline_method),
        'beta_d_assumption': beta_d_assumption,
        'interest_method': interest_method,
        'start': start,
        'end': end,
        'dsa_model': dsa_model,  # Store DSA model for DSA scenarios
        'mtp_anchors': mtp_anchors,  # Store MTP anchors for DSA scenarios
    }
    
    model_class.basedf = result
    model_class.lastdf = result
    return result


def run_scenario_analysis(
    baseline_result,
    model_class,
    scenario_shocks,
    scenario_name,
    shock_persistence='return_to_baseline',
    start=None,  # Will inherit from baseline if not specified
    end=None,    # Will inherit from baseline if not specified
    max_iterations=1000000,
    invert_maxiter=1000000,    
    silent=1,
    allow_fixed_shocks=False,  # NEW parameter
):
    """Run scenario analysis based on baseline specifications.
    
    This function requires shocks to be specified. The output gap closing timing
    is dynamic and based on when policy changes actually end:
    - Output gap closes from final_policy_change_year+1 to final_policy_change_year+3
    - Uses demand-side instruments (error-term) to gradually close the gap
    - Correctly handles all persistence modes (plateau, copy_last) and interpret modes (absolute, delta)
    
    For DSA_MTP baselines, the gap closure timing is automatically inherited from the
    DSA model's adjustment period:
    - Output gap closes from adjustment_end_year+1 to adjustment_end_year+3
    - Long-term targeting runs from adjustment_end_year+4 to end_year
    - No additional parameters needed - timing is automatically determined from the baseline
    
    The function automatically inherits all baseline options (baseline_method, beta_d_assumption, etc.)
    
    Parameters:
    -----------
    allow_fixed_shocks : bool, optional
        If True, allows shocking of normally fixed variables like U_TREND.
        When enabled, U_TREND shocks are pre-processed by temporarily unfixing,
        applying shocks directly to the data, and re-fixing the variable.
        
    Examples:
    --------
    # Standard scenario (gap closes after shocks)
    sce = run_scenario_analysis(baseline_result, model_class, measures, 'scenario')
    
    # DSA_MTP scenario - automatically uses DSA adjustment period
    sce = run_scenario_analysis(baseline_result, model_class, measures, 'scenario')
    # If DSA has 4-year adjustment period: gap closes in years 6-8 (if start=2025)
    # If DSA has 7-year adjustment period: gap closes in years 9-11 (if start=2025)
    
    # U_TREND shocking scenario
    sce = run_scenario_analysis(baseline_result, model_class, measures, 'scenario', 
                               allow_fixed_shocks=True)
    """
    
    # Inherit baseline options
    if not hasattr(model_class, 'baseline_options'):
        raise ValueError("Baseline options not found. Please run initialize_model first.")
    
    baseline_options = model_class.baseline_options
    baseline_method = baseline_options['baseline_method']
    beta_d_assumption = baseline_options['beta_d_assumption']
    
    # Use inherited start/end years if not specified
    if start is None:
        start = baseline_options['start']
    if end is None:
        end = baseline_options['end']
    
        debug_print_info("Inheriting baseline options", f"method={baseline_method}, beta_d={beta_d_assumption}")
    
    # 1) Take on the baseline result as the basedf
    model_class.basedf = baseline_result
    model_class.lastdf = baseline_result
    
    # 2) Apply scenario shocks to this baseline data
    if allow_fixed_shocks:
        scenario_data, variable_period_df = apply_scenario_shocks(
            baseline_result, scenario_shocks, shock_persistence=shock_persistence, 
            start_year=start, end_year=end, model_class=model_class
        )
    else:
        scenario_data, variable_period_df = apply_scenario_shocks(
            baseline_result, scenario_shocks, shock_persistence=shock_persistence, 
            start_year=start, end_year=end
        )
    
    # Determine the output-gap closure schedule window in the simplest, robust way:
    # - If there are NO policy shocks at all → treat as "no-shock" case and close the gap
    #   in years t+3..t+5 (so final_shock_year = t+2)
    # - If there ARE policy shocks → close the gap in the 3 years right after the last
    #   year with a provided (non-zero) policy change. We approximate this by taking the
    #   maximum number of provided periods across shocks (ignoring persistence extension),
    #   exactly as before, to keep behavior simple and transparent.
    if not variable_period_df.empty:
        max_shock_periods = 0
        debug_print_info("Shock period counting", "Per variable:")
        for shock_spec in scenario_shocks:
            if isinstance(shock_spec, dict) and 'values' in shock_spec:
                var_name = shock_spec['var']
                num_periods = len(shock_spec['values'])
                max_shock_periods = max(max_shock_periods, num_periods)
                debug_print_info(f"  {var_name}", f"{num_periods} periods")
            elif isinstance(shock_spec, (list, tuple)) and len(shock_spec) == 2:
                var_name = shock_spec[0]
                num_periods = len(shock_spec[1])  # values
                max_shock_periods = max(max_shock_periods, num_periods)
                debug_print_info(f"  {var_name}", f"{num_periods} periods")

        final_shock_year = start + max_shock_periods - 1
        debug_print_info("Policy changes end", f"in year {final_shock_year} (max shock periods: {max_shock_periods})")
        debug_print_info("Output gap closing", f"from year {final_shock_year + 1} to {final_shock_year + 3}")
    else:
        # No policy shocks detected → schedule automatic closure for years t+3..t+5
        final_shock_year = start + 2
        debug_print_info("No policy shocks detected", f"Closing output gap from year {start + 3} to {start + 5}")
    
    
    # Display applied shocks in a nice table format
    debug_print_section(f"SCENARIO: {scenario_name} | Shock Persistence: {shock_persistence}")
    
    # Display the accumulated shocks using the returned DataFrame
    if not variable_period_df.empty:
        from IPython.display import display
        display(variable_period_df)
    else:
        # Even with no shocks, we proceed with the automatic output-gap closure schedule (t+3..t+5)
        debug_print("No shocks applied - proceeding with automatic output-gap closure schedule")
        debug_print("="*60)
    
    # Use inherited baseline method instead of checking BETA_D
    baseline_lower = baseline_method.lower()
    is_eucam = (baseline_lower == 'eucam')
    is_dsa = (baseline_lower in ('dsa', 'dsa_mtp'))
    
    # Override final_shock_year for DSA_MTP baselines - automatically inherit from DSA model
    if baseline_lower == 'dsa_mtp':
        dsa_model = baseline_options.get('dsa_model')
        if dsa_model is not None:
            # Use the DSA model's adjustment period to determine gap closure timing
            adjustment_end_year = getattr(dsa_model, 'adjustment_end_year', None)
            if adjustment_end_year is not None:
                final_shock_year = adjustment_end_year
                debug_print_info("DSA_MTP automatic timing", f"Using DSA adjustment_end_year={adjustment_end_year}")
                debug_print_info("Output gap closing", f"from year {adjustment_end_year + 1} to {adjustment_end_year + 3}")
            else:
                debug_print_warning("DSA_MTP timing", "adjustment_end_year not found in DSA model, using shock-based timing")
        else:
            debug_print_warning("DSA_MTP timing", "DSA model not found, using shock-based timing")
    
    # 3) If own: solve the model from start to end
    # 4) If EUCAM: solve the model sequentially with targets as in baseline
    # 5) If DSA: use DSA-specific scenario targeting with selective MTP anchor preservation
    if is_dsa:
        # DSA method: use DSA-specific scenario targeting with selective MTP anchor preservation
        result = model_class(scenario_data, start, end, max_iterations=max_iterations, silent=silent)
        result = apply_targets_sequentially_scenario_dsa(
            result,
            model_class,
            start_year=start,
            end_year=end,
            invert_maxiter=invert_maxiter,
            max_iterations=max_iterations,
            silent=silent,
            final_shock_year=final_shock_year,
            beta_d_assumption=beta_d_assumption,
            dsa_model=baseline_options.get('dsa_model'),
            mtp_anchors=baseline_options.get('mtp_anchors'),
        )
    elif not is_eucam:
        # Own method: first solve directly from start to end, then ALWAYS run the universal
        # output-gap closure routine so the gap closes either after shocks (Y*+1..Y*+3) or, if
        # there are no shocks, in years t+3..t+5.
        result = model_class(scenario_data, start, end, max_iterations=max_iterations, silent=silent)
        result = apply_targets_sequentially_scenario(
            result,
            model_class,
            start_year=start,
            end_year=end,
            invert_maxiter=invert_maxiter,
            max_iterations=max_iterations,
            silent=silent,
            final_shock_year=final_shock_year,
            beta_d_assumption=beta_d_assumption,
        )
    else:
        # EUCAM method: solve sequentially with targets as in baseline
        # First solve the model initially
        result = model_class(scenario_data, start, end, max_iterations=max_iterations, init=True, silent=silent, reset_options=True)
        
        # Apply targets sequentially with scenario context
        result = apply_targets_sequentially_scenario(
            result, model_class, start_year=start, end_year=end, invert_maxiter=invert_maxiter, silent=silent, max_iterations=max_iterations, final_shock_year=final_shock_year, beta_d_assumption=beta_d_assumption
        )
    
    # Store solution and return
    model_class.keep_solutions[scenario_name] = result
    model_class.lastdf = result
    result.name = scenario_name
    
    return result


def apply_targets_sequentially_baseline(result, data, model_class, invert_maxiter, start_year, end_year, LT_baseline_method):
    """Apply targets sequentially for baseline: short-term, medium-term, long-term."""
    
    time_horizon = end_year - start_year
    
    # Calculate targets and instruments for baseline
    target_bl_ST = data.loc[start_year:start_year+1, ["Y_STAR", "Y_D"]].copy()
    target_bl_MT = data.loc[start_year+2:start_year+4, ["Y_STAR", "Y_GAP"]].copy()
    target_bl_LT = data.loc[start_year+5:end_year, ["Y_GAP"]].copy()
    target_bl_LT.loc[:, "Y_GAP"] = 0
    
    instruments_ST = ["EPS_SR", "EPS_Y_D"]
    instruments_MT = ["EPS_SR", "EPS_Y_D"]
    instruments_LT = ["EPS_Y_D"]
    
    # Add AR24 long-term targeting if specified
    if LT_baseline_method == 'AR24':
        # Load LT growth rates data (single sheet with all countries)
        import pandas as pd
        from pathlib import Path
        
        lt_growth_filepath = Path("../02_Daten") / "LT growth rates.xlsx"
        lt_growth_data = pd.read_excel(lt_growth_filepath, sheet_name="Growth", index_col=0)
        
        if lt_growth_data is not None:
            # Get country name from the data loading (this should be passed as parameter)
            # For now, we'll need to determine the country - this should be improved
            # by passing the country name as a parameter to this function
            country_name = "Germany"  # This should be passed as parameter
            
            # Filter LT growth data for the specific country and PO growth
            country_po_data = lt_growth_data[
                (lt_growth_data['Country'] == country_name) & 
                (lt_growth_data['GDP/PO'] == 'PO growth')
            ]
            
            if not country_po_data.empty:
                # Get PO growth rates for the long-term years
                lt_years = range(start_year+5, end_year+1)
                for year in lt_years:
                    if year in country_po_data.columns:
                        po_growth_rate = country_po_data[year].iloc[0]
                        target_bl_LT.loc[year, "G_Y_STAR"] = po_growth_rate
                
                # Add EPS_SR as second instrument for long-term
                instruments_LT = ["EPS_SR", "EPS_Y_D"]
                
                debug_print_info("AR24 LT targeting", f"Applied PO growth rates for {country_name} from AR24 data")
            else:
                debug_print_warning("AR24 LT targeting", f"No PO growth data found for {country_name}")
        else:
            debug_print_warning("AR24 LT targeting", "LT growth rates data not available, using default LT targeting")
    

    with model_class.set_smpl(start_year, start_year+1):
        result = model_class.invert(
            result, target_bl_ST, instruments_ST, defaultconv=1e-1, maxiter=invert_maxiter
        )
    
    # Only run medium-term if horizon is at least 3 years
    if time_horizon >= 2:
        with model_class.set_smpl(start_year+2, start_year+4):
            result = model_class.invert(
                result, target_bl_MT, instruments_MT, defaultconv=1, maxiter=invert_maxiter
            )

    # Only run long-term if horizon is at least 6 years
    if time_horizon >= 5:
        with model_class.set_smpl(start_year+5, end_year):
            result = model_class.invert(
                result, target_bl_LT, instruments_LT, defaultconv=1e-12, maxiter=invert_maxiter
            )
    
    return result


def apply_targets_sequentially_baseline_dsa(result, data, model_class, invert_maxiter, start_year, end_year, dsa_model):
    """Apply DSA growth-rate targets for Y (real GDP) and Y_STAR (potential) over entire horizon.

    Targets PI, G_Y_D, G_Y_STAR for all years start_year..end_year
    """
    import pandas as pd

    years = list(range(start_year, end_year + 1))
    def _ser(name):
        s_years = list(range(dsa_model.start_year, dsa_model.end_year + 1))
        arr = getattr(dsa_model, name)
        ser = pd.Series(arr, index=s_years)
        return ser.reindex(years)

    tgt_pi = _ser('pi')
    tgt_rgdp = _ser('rgdp')
    tgt_rgdp_pot = _ser('rgdp_pot') 

    # Target all three variables over entire time horizon
    with model_class.set_smpl(start_year, end_year):
        targets = pd.DataFrame({
            'PI': tgt_pi.loc[start_year:end_year],
            'Y_D': tgt_rgdp.loc[start_year:end_year] * 10**9,
            'Y_STAR': tgt_rgdp_pot.loc[start_year:end_year] * 10**9,
        })
        result = model_class.invert(
            result,
            targets,
            instruments=['EPS_PI', 'EPS_Y_D', 'EPS_SR'],
            defaultconv=1e-1,
            maxiter=invert_maxiter,
        )

    return result

def apply_targets_sequentially_scenario(result, model_class, start_year, end_year, invert_maxiter, max_iterations, silent, final_shock_year, beta_d_assumption):
    """Apply targets sequentially for scenario: short-term, medium-term, long-term.
    
    This function closes the output gap dynamically based on when shocks end:
    - Output gap closes from final_shock_year+1 to final_shock_year+3
    - Uses fiscal policy instruments to gradually close the gap
    
    Parameters:
        beta_d_assumption: str, either 'estimated' (use baseline BETA_D) or 'zero' (set BETA_D=0)
        LT_baseline_method: str, either 'own' (use current long-term logic) or 'AR24' (use AR24 long-term growth rates)
    """

    time_horizon = end_year - start_year
    
    debug_print_info("Shocks applied - closing output gap", f"from year {final_shock_year + 1} to {final_shock_year + 3}")
    
    # Apply beta_d assumption during output gap closure
    if beta_d_assumption == 'zero':
        debug_print_info("Setting BETA_D = 0 during output gap closure", f"years {final_shock_year + 1} to {final_shock_year + 3}")
        # Set BETA_D to zero for the gap closure period
        result.loc[final_shock_year + 1:final_shock_year + 3, 'BETA_D'] = 0
    else:
        debug_print_info("Using estimated BETA_D values during output gap closure", "")
    
    sce_gap = result.loc[final_shock_year, "Y_GAP"]  # Output gap at end of shock period

    # Calculate targets for shock case: close gap from final_shock_year + 1 to final_shock_year + 3
    target_sce_MT = result.loc[final_shock_year + 1 : final_shock_year + 3, ['Y_GAP']].copy()  
    target_sce_MT.loc[final_shock_year + 1, 'Y_GAP'] = (2/3) * sce_gap  # 2027: 2/3 of gap
    target_sce_MT.loc[final_shock_year + 2, 'Y_GAP'] = (1/3) * sce_gap  # 2028: 1/3 of gap
    target_sce_MT.loc[final_shock_year + 3, 'Y_GAP'] = 0  # 2029: close gap
    
    target_sce_LT = result.loc[final_shock_year+4:end_year, ["Y_GAP"]].copy()
    target_sce_LT.loc[:, "Y_GAP"] = 0

    instruments_sce_MT = ["EPS_Y_D"]
    instruments_sce_LT = ["EPS_Y_D"]
    
    # Note: AR24 targeting is NOT applied in scenarios
    # Scenarios use simple targeting: close output gap, then Y_D = Y_STAR

    # Model solving logic for shock case
    with model_class.set_smpl(start_year, final_shock_year): # e.g., 2025-2029
        result = model_class(result, max_iterations=max_iterations)
    
    # Only run "medium-term" (post-shock period) if horizon is longer than the shock period
    if time_horizon > final_shock_year - start_year:
        with model_class.set_smpl(final_shock_year + 1, final_shock_year + 3):  # e.g., 2030-3032
            result = model_class.invert(
                result, 
                target_sce_MT, 
                instruments_sce_MT, 
                silent=silent, 
                defaultconv=1e-12, 
                maxiter=invert_maxiter
            )

    # Only run "long-term" (post-shock period) if horizon is longer than the shock period + output gap closure period
    if time_horizon > final_shock_year - start_year + 3:
        with model_class.set_smpl(final_shock_year + 4, end_year):
            result = model_class.invert(
                result, target_sce_LT, instruments_sce_LT, defaultconv=1e-12, maxiter=invert_maxiter
            )
    
    return result


def apply_targets_sequentially_scenario_dsa(result, model_class, start_year, end_year, invert_maxiter, max_iterations, silent, final_shock_year, beta_d_assumption, dsa_model, mtp_anchors=None):
    """Apply DSA targeting for scenarios with selective MTP anchor preservation.
    
    This function preserves only rg and pi MTP anchors, allowing rg_pot to adjust endogenously.
    It targets Y_D from DSA (with MTP-anchored rg) but lets Y_STAR adjust endogenously.
    
    The final_shock_year parameter should already be set to the DSA adjustment_end_year
    by the calling function for proper gap closure timing.
    
    Parameters:
        result: Model result DataFrame
        model_class: Model class instance
        start_year: Start year for targeting
        end_year: End year for targeting
        invert_maxiter: Maximum iterations for inversion
        max_iterations: Maximum iterations for model solving
        silent: Silent mode flag
        final_shock_year: Final year with shocks (should be DSA adjustment_end_year)
        beta_d_assumption: BETA_D assumption ('estimated' or 'zero')
        dsa_model: DSA model instance
        mtp_anchors: MTP anchors dictionary (will be filtered to rg, pi only)
    """
    import pandas as pd
    import numpy as np
    
    # Step 1: Apply selective MTP anchors (rg, pi only)
    if mtp_anchors:
        try:
            from integration import apply_selective_mtp_anchors_to_dsa
            apply_selective_mtp_anchors_to_dsa(
                dsa_model, 
                anchors=mtp_anchors, 
                preserve_keys=['rg', 'pi'],  # Only preserve demand side
                inplace=True
            )
            debug_print_info("Applied selective MTP anchors", "rg and pi preserved, rg_pot endogenous")
        except Exception as e:
            debug_print_warning("Selective MTP anchors application failed", str(e))
    
    # Step 2: Extract DSA targets (rg_pot will be endogenous, not anchored)
    years = list(range(start_year, end_year + 1))
    def _ser(name):
        s_years = list(range(dsa_model.start_year, dsa_model.end_year + 1))
        arr = getattr(dsa_model, name)
        ser = pd.Series(arr, index=s_years)
        return ser.reindex(years)

    tgt_pi = _ser('pi')      # MTP-anchored inflation
    tgt_rgdp = _ser('rgdp')  # MTP-anchored real GDP level
    # Note: rgdp_pot will be endogenous, not extracted from DSA

    # Step 3: Target only Y_D and PI (not Y_STAR)
    targets = pd.DataFrame({
        'PI': tgt_pi.loc[start_year:end_year],
        'Y_D': tgt_rgdp.loc[start_year:end_year] * 10**9,  # MTP-anchored
        # Y_STAR is NOT targeted - allows endogenous adjustment
    })

    # Step 4: Use different instruments (no EPS_SR for Y_STAR targeting)
    instruments = ['EPS_PI', 'EPS_Y_D']  # No EPS_SR since Y_STAR is endogenous

    time_horizon = end_year - start_year
    
    # Handle zero shock scenarios
    if final_shock_year == start_year + 2:  # No shocks detected
        debug_print_info("Zero shock DSA scenario", "Applying selective DSA targeting only")
        # Zero shock scenario - apply selective DSA targeting only
        with model_class.set_smpl(start_year, end_year):
            result = model_class.invert(
                result, targets, 
                instruments=instruments,
                defaultconv=1e-1, maxiter=invert_maxiter
            )
        return result
    
    # Handle non-zero shock scenarios
    debug_print_info("Non-zero shock DSA scenario", f"Closing output gap from year {final_shock_year + 1} to {final_shock_year + 3}")
    
    # Apply beta_d assumption during output gap closure
    if beta_d_assumption == 'zero':
        debug_print_info("Setting BETA_D = 0 during output gap closure", f"years {final_shock_year + 1} to {final_shock_year + 3}")
        # Set BETA_D to zero for the gap closure period
        result.loc[final_shock_year + 1:final_shock_year + 3, 'BETA_D'] = 0
    else:
        debug_print_info("Using estimated BETA_D values during output gap closure", "")
    
    sce_gap = result.loc[final_shock_year, "Y_GAP"]  # Output gap at end of shock period

    # Calculate targets for shock case: close gap from final_shock_year + 1 to final_shock_year + 3
    target_sce_MT = result.loc[final_shock_year + 1 : final_shock_year + 3, ['Y_GAP']].copy()  
    target_sce_MT.loc[final_shock_year + 1, 'Y_GAP'] = (2/3) * sce_gap  # 2/3 of gap
    target_sce_MT.loc[final_shock_year + 2, 'Y_GAP'] = (1/3) * sce_gap  # 1/3 of gap
    target_sce_MT.loc[final_shock_year + 3, 'Y_GAP'] = 0  # close gap
    
    target_sce_LT = result.loc[final_shock_year+4:end_year, ["Y_GAP"]].copy()
    target_sce_LT.loc[:, "Y_GAP"] = 0

    instruments_sce_MT = ["EPS_Y_D"]
    instruments_sce_LT = ["EPS_Y_D"]

    # Model solving logic for shock case
    with model_class.set_smpl(start_year, final_shock_year): # e.g., 2025-2029
        result = model_class(result, max_iterations=max_iterations)
    
    # Only run "medium-term" (post-shock period) if horizon is longer than the shock period
    if time_horizon > final_shock_year - start_year:
        with model_class.set_smpl(final_shock_year + 1, final_shock_year + 3):  # e.g., 2030-3032
            result = model_class.invert(
                result, 
                target_sce_MT, 
                instruments_sce_MT, 
                silent=silent, 
                defaultconv=1e-12, 
                maxiter=invert_maxiter
            )

    # Only run "long-term" (post-shock period) if horizon is longer than the shock period + output gap closure period
    if time_horizon > final_shock_year - start_year + 3:
        with model_class.set_smpl(final_shock_year + 4, end_year):
            result = model_class.invert(
                result, target_sce_LT, instruments_sce_LT, defaultconv=1e-12, maxiter=invert_maxiter
            )
    
    return result


def apply_scenario_shocks(baseline_result, scenario_shocks, shock_persistence, start_year, end_year, model_class=None):
    """Apply scenario shocks to baseline data.
    
    Parameters:
    -----------
    model_class : ModelClass, optional
        Model class instance needed for unfixing fixed variables during shocks
    """

    import pandas as pd
    import numpy as np

    # CHANGED: Support mixed shock types (level vs error) with per-variable persistence semantics.
    # - Backward-compatible with legacy inputs (list of (var, values) or dict var->values)
    # - New: accept list of dicts with keys: var, values, persist (bool), persist_mode ('copy_last'|'plateau'),
    #         kind ('level'|'error'), and optional start_offset (int)
    #   * 'plateau' for errors => extend zeros after the provided values (avoids cumulative drift)
    #   * 'copy_last' => extend the last provided value through end_year

    scenario_data = baseline_result.copy()

    def _infer_kind(name: str) -> str:
        # Treat V_*_STAR as level (additive to structural rates), not as an accumulating error
        if name.endswith('_STAR'):
            return 'level'
        if name.startswith('EPS_'):
            return 'error'
        if name.startswith('V_'):
            # Generic V_ shocks to shares are typically level add-ons in this model
            return 'level'
        return 'level'

    # Normalize inputs into a list of spec dicts
    specs = []
    if isinstance(scenario_shocks, dict):
        # legacy dict: var -> values
        for var, vals in scenario_shocks.items():
            specs.append({
                'var': var,
                'values': list(vals),
                'persist': (shock_persistence == 'persist'),
                'persist_mode': None,  # derive default later
                'kind': _infer_kind(var),
                'start_offset': 0,
            })
    else:
        # list-based inputs: can be tuples (legacy) or dicts (new)
        for item in list(scenario_shocks):
            if isinstance(item, dict) and 'var' in item and 'values' in item:
                spec = {
                    'var': item['var'],
                    'values': list(item['values']),
                    'persist': bool(item.get('persist', (shock_persistence == 'persist'))),
                    'persist_mode': item.get('persist_mode'),
                    'kind': item.get('kind') or _infer_kind(item['var']),
                    'start_offset': int(item.get('start_offset', 0)),
                    'interpret': item.get('interpret', 'absolute'),  # 'absolute' | 'delta'
                }
                specs.append(spec)
            else:
                # legacy (var, values)
                var, vals = item
                specs.append({
                    'var': var,
                    'values': list(vals),
                    'persist': (shock_persistence == 'persist'),
                    'persist_mode': None,
                    'kind': _infer_kind(var),
                    'start_offset': 0,
                    'interpret': 'absolute',
                })

    # NEW: Check for U_TREND shocks and handle them specially
    utrend_shocked = False
    utrend_shock_spec = None
    
    for spec in specs:
        if spec['var'] == 'U_TREND':
            utrend_shocked = True
            utrend_shock_spec = spec
            break
    
    # NEW: Handle U_TREND shocks specially
    if utrend_shocked and model_class is not None:
        debug_print_info("U_TREND shock detected", "Pre-processing U_TREND shocks")
        
        # Step 1: Unfix U_TREND temporarily
        scenario_data = model_class.unfix(scenario_data, pat="U_TREND", start=start_year, end=end_year)
        
        # Step 2: Apply U_TREND shocks directly to the data
        utrend_values = utrend_shock_spec['values']
        interpret = utrend_shock_spec.get('interpret', 'absolute')
        persist = utrend_shock_spec.get('persist', False)
        persist_mode = utrend_shock_spec.get('persist_mode', 'copy_last')
        
        # Apply shocks to U_TREND values
        for i, value in enumerate(utrend_values):
            year = start_year + i
            if year <= end_year:
                if interpret == 'delta':
                    # Delta: add to existing value
                    scenario_data.loc[year, 'U_TREND'] += value
                else:
                    # Absolute: set to new value
                    scenario_data.loc[year, 'U_TREND'] = value
        
        # Handle persistence if specified
        if persist and len(utrend_values) > 0:
            last_value = utrend_values[-1]
            last_year = start_year + len(utrend_values) - 1
            if persist_mode == 'copy_last':
                for year in range(last_year + 1, end_year + 1):
                    if interpret == 'delta':
                        scenario_data.loc[year, 'U_TREND'] += last_value
                    else:
                        scenario_data.loc[year, 'U_TREND'] = last_value
        
        # Step 3: Re-fix U_TREND immediately
        scenario_data = model_class.fix(scenario_data, pat="U_TREND", start=start_year, end=end_year, silent=1)
        
        debug_print_info("U_TREND pre-processing complete", "U_TREND shocks applied and variable re-fixed")
        
        # Remove U_TREND from normal shock processing
        specs = [spec for spec in specs if spec['var'] != 'U_TREND']

    # Determine per-variable totals by aligning and summing
    # Default persist_mode: level -> copy_last; error -> plateau (to avoid cumulative drift)
    horizon_len = end_year - start_year + 1
    var_to_series = {}
    for spec in specs:
        var = spec['var']
        kind = spec['kind']
        vals = list(spec['values'])
        start_offset = max(0, int(spec['start_offset']))
        persist = bool(spec['persist'])
        persist_mode = spec['persist_mode']
        interpret = spec.get('interpret', 'absolute')
        if persist_mode is None:
            persist_mode = 'copy_last' if kind == 'level' else 'plateau'

        # Build full-length vector for this spec
        arr = np.zeros(horizon_len, dtype=float)
        insert_start = start_offset
        insert_end = min(horizon_len, start_offset + len(vals))
        if insert_start < horizon_len:
            if interpret == 'delta' and kind == 'error':
                # Convert desired total delta path (Δ) into innovations (ε) so that the state gap equals Δ each year
                # ε[t] = Δ[t] - Δ[t-1], with Δ[-1] = 0 at the start of the window
                if len(vals) > 0:
                    deltas = np.array(vals[: max(0, insert_end - insert_start)], dtype=float)
                    eps = np.zeros_like(deltas)
                    eps[0] = deltas[0]
                    if eps.size > 1:
                        eps[1:] = deltas[1:] - deltas[:-1]
                    arr[insert_start:insert_end] += eps
            else:
                trunc_vals = vals[: max(0, insert_end - insert_start)]
                if trunc_vals:
                    arr[insert_start:insert_end] += np.array(trunc_vals, dtype=float)
        # Handle persistence beyond provided values
        if persist and insert_end < horizon_len:
            if persist_mode == 'copy_last':
                last = float(vals[-1]) if vals else 0.0
                arr[insert_end:] = last
            elif persist_mode == 'plateau':
                # plateau for errors: extend zeros so level gap remains constant
                # (no additional flow added beyond the specified periods)
                pass

        # Accumulate per variable
        if var not in var_to_series:
            var_to_series[var] = arr
        else:
            var_to_series[var] = var_to_series[var] + arr

    # Build variable-period display table (trim trailing all-zeros columns for readability)
    if var_to_series:
        max_cols = horizon_len
        df_disp = pd.DataFrame({v: s for v, s in var_to_series.items()}).T
        # trim trailing all-zero columns
        nonzero_cols = (df_disp.abs().sum(axis=0) > 0)
        if nonzero_cols.any():
            last_col = np.where(nonzero_cols)[0].max()
            df_disp = df_disp.iloc[:, : last_col + 1]
        df_disp.columns = [f"Period {i+1}" for i in range(df_disp.shape[1])]
        variable_period_df = df_disp
    else:
        variable_period_df = pd.DataFrame()

    # Convert to upd() inputs and apply
    shocks_applied = False
    for var, arr in var_to_series.items():
        # find last non-zero index to shorten the upd window
        nz = np.where(np.abs(arr) > 0)[0]
        if nz.size == 0:
            continue
        shock_start = start_year
        
        # Check if this variable has copy_last persistence
        spec = next((s for s in specs if s['var'] == var), None)
        if spec and spec.get('persist_mode') == 'copy_last' and spec.get('persist', False):
            # For copy_last persistent shocks: apply to FULL horizon to ensure persistence
            shock_end = start_year + len(arr) - 1
            series_vals = arr
            debug_print_info(f"Applying persistent shock {var}", f"from {shock_start} to {shock_end} (full horizon)")
        else:
            # For non-persistent or plateau shocks: use original truncation logic
            shock_end = start_year + nz.max()
            series_vals = arr[: nz.max() + 1]
            debug_print_info(f"Applying non-persistent shock {var}", f"from {shock_start} to {shock_end}")
        
        shock_string = f"<{shock_start} {shock_end}> {var} + {' '.join([str(val) for val in series_vals])}"
        try:
            scenario_data = scenario_data.upd(shock_string)
            shocks_applied = True
        except Exception as e:
            debug_print_error(f"Error applying shock {shock_string}: {e}")
    
        # Warn if variable not present (keep legacy behavior of warning)
        if var not in baseline_result.columns:
            debug_print_warning(f"Variable {var} not found in baseline data")
    
    # Mark that shocks were applied (for default case detection)
    if shocks_applied:
        scenario_data._shocks_applied = True
    
    return scenario_data, variable_period_df
