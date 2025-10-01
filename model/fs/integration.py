"""
Integration helpers between FS model and DSA model.

Functions here do not alter core FS or DSA logic. They provide orchestrated
utilities to (a) pass FS potential to DSA while specifying an SPB path,
(b) compare binding SPB under baseline vs adjusted potential to quantify
fiscal space differences.
"""

from __future__ import annotations

import copy
from typing import Iterable, Optional, Tuple, Dict, Union, List

import numpy as np
import pandas as pd


def _series_from_dsa(dsa_model, var_name: str) -> pd.Series:
    """Return a pandas Series for a given DSA attribute using calendar years as index."""
    years = np.arange(dsa_model.start_year, dsa_model.end_year + 1)
    arr = getattr(dsa_model, var_name)
    if len(arr) != len(years):
        # pad/truncate defensively
        n = min(len(arr), len(years))
        years = years[:n]
        arr = arr[:n]
    return pd.Series(arr, index=years)


def apply_fs_potential_to_dsa(
    dsa_model,
    fs_df: pd.DataFrame,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    inplace: bool = True,
    *,
    use_smoothed_growth: bool = False,
    smooth_start_year: Optional[int] = None,
    smooth_end_year: Optional[int] = None,
    growth_periods: Optional[List[Dict[str, Union[int, float]]]] = None,
):
    """
    Overwrite DSA potential baseline with FS potential-related series from fs_df.

    Inputs:
    - fs_df: DataFrame containing FS results with columns 'Y_STAR' (level) and 'G_Y_STAR' (growth %).
    - start_year/end_year: range of years over which to overwrite DSA potential. Defaults to
      model horizon intersection.
    - inplace: modify the provided dsa_model, else operate on a deepcopy and return it.
    - use_smoothed_growth: if True, calculate a constant growth rate from smooth_start_year to 
      smooth_end_year and apply it instead of the original G_Y_STAR values.
    - smooth_start_year/smooth_end_year: years for calculating the constant growth rate.
      Defaults to start_year/end_year if not specified.
    - growth_periods: List of dictionaries defining multiple growth periods. Each dict should have
      'start_year', 'end_year', and 'growth_rate' keys. If provided, this overrides use_smoothed_growth.

    Returns: the modified dsa_model.
    """
    model = dsa_model if inplace else copy.deepcopy(dsa_model)

    if start_year is None:
        start_year = model.start_year
    if end_year is None:
        end_year = model.end_year

    # CHANGED: Clamp application years to overlap of DSA horizon and fs_df index.
    # This avoids out-of-bounds when DSA runs longer than FS or vice versa, and emits
    # a clear warning if the overlap is shorter than typical DSA usage.
    years_full = list(range(model.start_year, model.end_year + 1))
    fs_years = sorted([int(y) for y in fs_df.index if isinstance(y, (int, np.integer))])
    overlap_start = start_year if start_year is not None else model.start_year
    overlap_end = end_year if end_year is not None else model.end_year
    years = [y for y in range(overlap_start, overlap_end + 1) if (y in years_full and y in fs_years)]
    if not years:
        import warnings as _warnings
        _warnings.warn(
            "FS→DSA potential: no overlapping years between FS results and DSA horizon; "
            "skipping potential injection. For best results, ensure overlapping years.",
            RuntimeWarning,
        )
        return model
    years_idx = [y - model.start_year for y in years]

    # Handle growth rate options
    if growth_periods is not None:
        # Use multiple growth periods
        g_y_star_fs = pd.Series(index=years, dtype=float)
        
        for period in growth_periods:
            period_start = period['start_year']
            period_end = period['end_year']
            period_growth_rate = period['growth_rate']
            
            # Apply growth rate to years within this period
            for year in years:
                if period_start <= year <= period_end:
                    g_y_star_fs.loc[year] = period_growth_rate
        
        # Fill any missing years with original FS growth rates
        missing_years = g_y_star_fs.isna()
        if missing_years.any():
            g_y_star_fs.loc[missing_years] = fs_df.loc[missing_years.index[missing_years], 'G_Y_STAR'].astype(float)
            
    elif use_smoothed_growth:
        # Set smooth years if not specified
        if smooth_start_year is None:
            smooth_start_year = start_year
        if smooth_end_year is None:
            smooth_end_year = end_year
        
        # Calculate constant growth rate from start to end values
        start_value = fs_df.loc[smooth_start_year, 'Y_STAR']
        end_value = fs_df.loc[smooth_end_year, 'Y_STAR']
        years_span = smooth_end_year - smooth_start_year
        
        if years_span > 0:
            total_growth_factor = end_value / start_value
            constant_growth_rate = (total_growth_factor ** (1/years_span)) - 1
            # Convert to percentage
            constant_growth_rate_pct = constant_growth_rate * 100
        else:
            # If same year, use the original growth rate
            constant_growth_rate_pct = fs_df.loc[smooth_start_year, 'G_Y_STAR']
        
        # Create smoothed growth rate series
        g_y_star_fs = pd.Series([constant_growth_rate_pct] * len(years), index=years)
    else:
        # Build new potential arrays from FS using rates, independent of units
        # FS: G_Y_STAR is % growth; Y_STAR is level (not used for alignment here)
        g_y_star_fs = fs_df.loc[years, 'G_Y_STAR'].astype(float)

    # Assign to baseline and current potential arrays so resets use our values
    for i, y in enumerate(years_idx):
        gr = float(g_y_star_fs.iloc[i])
        model.rg_pot_bl[y] = gr
        model.rg_pot[y] = gr
        # Rebuild potential level from previous period using growth rate to preserve units
        if y == 0:
            # keep initial baseline level unchanged
            model.rgdp_pot_bl[y] = model.rgdp_pot_bl[y]
            model.rgdp_pot[y] = model.rgdp_pot[y]
        else:
            model.rgdp_pot_bl[y] = model.rgdp_pot_bl[y-1] * (1.0 + gr/100.0)
            model.rgdp_pot[y] = model.rgdp_pot[y-1] * (1.0 + gr/100.0)

    return model


def apply_mtp_anchors_to_dsa(
    dsa_model,
    anchors: Dict[str, Union[pd.Series, Dict[int, float], Iterable[float]]],
    inplace: bool = True,
    *,
    force_gap_closure: bool = True,
    gap_closure_year: Optional[int] = None,
    blend_years: int = 2,
) -> object:
    """
    Apply country MTP anchors to the DSA baseline for selected macro variables.

    This function modifies ONLY baseline series (and their consistent derivatives):
      - Real GDP growth (rg_bl) and level (rgdp_bl)
      - Potential GDP growth (rg_pot_bl) and level (rgdp_pot_bl)
      - Inflation (pi)
      - Output gap baseline (output_gap_bl)
      - Nominal growth baseline (ng_bl) and level (ngdp_bl)

    Inputs (all optional inside anchors):
      anchors = {
        'rg':    pd.Series|dict|iterable  # real GDP growth in %, by year
        'rg_pot':pd.Series|dict|iterable  # potential GDP growth in %, by year
        'pi':    pd.Series|dict|iterable  # GDP deflator inflation in %, by year
      }

    Behavior:
      - Anchors can be partial (some years missing). Missing values are filled with current DSA baseline.
      - If an anchor key is omitted, the corresponding baseline remains unchanged.
      - Level paths (rgdp*_bl, ngdp_bl) are rebuilt recursively from t=1 onward using existing t=0 level.

    Parameters:
      - force_gap_closure: if True and 'rg' not provided in anchors, align real growth to potential
        after a cutoff so that the baseline output gap closes and stays at zero in the long run.
      - gap_closure_year: first calendar year from which to begin aligning real growth to potential.
        Defaults to (adjustment_end_year + 1).
      - blend_years: number of years to blend rg_bl toward rg_pot_bl starting at gap_closure_year
        before fully matching potential growth thereafter. Set 0 for immediate alignment.

    Returns: the modified dsa_model (same object if inplace=True).
    """
    model = dsa_model if inplace else copy.deepcopy(dsa_model)

    years = list(range(model.start_year, model.end_year + 1))
    n = len(years)

    def _full_series(value, default_series: pd.Series) -> pd.Series:
        if value is None:
            return default_series.copy()
        if isinstance(value, pd.Series):
            ser = value.copy()
        elif isinstance(value, dict):
            ser = pd.Series(value)
        elif isinstance(value, (list, tuple)):
            arr = list(value)
            if len(arr) != len(default_series.index):
                # If a raw iterable is provided, require full length to avoid misalignment
                raise ValueError("Iterable anchors must have full model horizon length; use a Series/dict keyed by year for partial anchors.")
            ser = pd.Series(arr, index=default_series.index)
        else:
            raise TypeError("Anchor must be a pandas Series, dict, or iterable of floats.")
        ser = ser.reindex(default_series.index)
        # Fill gaps with defaults to keep baseline intact where unspecified
        ser = ser.astype(float)
        ser = ser.where(~ser.isna(), default_series)
        return ser

    # Build default baselines as Series for easy alignment
    idx_years = pd.Index(years, name='y')
    rg_bl_default = pd.Series(getattr(model, 'rg_bl'), index=idx_years)
    rgdp_bl_default = pd.Series(getattr(model, 'rgdp_bl'), index=idx_years)
    rg_pot_bl_default = pd.Series(getattr(model, 'rg_pot_bl'), index=idx_years)
    rgdp_pot_bl_default = pd.Series(getattr(model, 'rgdp_pot_bl'), index=idx_years)
    pi_default = pd.Series(getattr(model, 'pi'), index=idx_years)
    ng_bl_default = pd.Series(getattr(model, 'ng_bl'), index=idx_years)
    ngdp_bl_default = pd.Series(getattr(model, 'ngdp_bl'), index=idx_years)

    # Normalize provided anchors to full-year Series
    rg_anchor = _full_series(anchors.get('rg') if anchors else None, rg_bl_default)
    rg_pot_anchor = _full_series(anchors.get('rg_pot') if anchors else None, rg_pot_bl_default)
    pi_anchor = _full_series(anchors.get('pi') if anchors else None, pi_default)

    # Start from existing baseline levels at t0
    rgdp_bl = rgdp_bl_default.copy()
    rgdp_pot_bl = rgdp_pot_bl_default.copy()

    # Update baseline growth series according to anchors
    rg_bl = rg_bl_default.copy()
    rg_bl.loc[years] = rg_anchor.values

    rg_pot_bl = rg_pot_bl_default.copy()
    rg_pot_bl.loc[years] = rg_pot_anchor.values

    pi = pi_default.copy()
    pi.loc[years] = pi_anchor.values

    # Optionally force long-run output gap closure by aligning rg_bl to rg_pot_bl
    if force_gap_closure and (('rg' not in anchors) or (anchors.get('rg') is None)):
        # Determine when to start aligning
        cutoff_year = gap_closure_year if gap_closure_year is not None else dsa_model.adjustment_end_year + 1
        # Build index mapping year->position; clamp to bounds
        if cutoff_year <= years[0]:
            cutoff_idx = 0
        elif cutoff_year > years[-1]:
            cutoff_idx = len(years)  # nothing to do
        else:
            cutoff_idx = years.index(cutoff_year)

        if cutoff_idx < len(years):
            blend_len = max(0, int(blend_years))
            pre_rg = rg_bl.copy()
            # Blend from cutoff_idx over blend_len years toward rg_pot_bl
            for j in range(blend_len):
                t = cutoff_idx + j
                if t >= len(years):
                    break
                w = (j + 1) / (blend_len + 1)
                rg_bl.iloc[t] = (1 - w) * pre_rg.iloc[t] + w * rg_pot_bl.iloc[t]
            # After blend window, fully align to potential growth
            if cutoff_idx + blend_len < len(years):
                rg_bl.iloc[cutoff_idx + blend_len:] = rg_pot_bl.iloc[cutoff_idx + blend_len:]

    # Rebuild level baselines from t=1 onward to preserve initial scale
    for i in range(1, n):
        rgdp_bl.iloc[i] = rgdp_bl.iloc[i - 1] * (1.0 + rg_bl.iloc[i] / 100.0)
        rgdp_pot_bl.iloc[i] = rgdp_pot_bl.iloc[i - 1] * (1.0 + rg_pot_bl.iloc[i] / 100.0)

    # Output gap baseline from updated levels
    output_gap_bl = (rgdp_bl / rgdp_pot_bl - 1.0) * 100.0

    # Nominal growth baseline and nominal GDP baseline
    ng_bl = ((1.0 + rg_bl / 100.0) * (1.0 + pi / 100.0) * 100.0) - 100.0
    ngdp_bl = ngdp_bl_default.copy()
    for i in range(1, n):
        ngdp_bl.iloc[i] = ngdp_bl.iloc[i - 1] * (1.0 + ng_bl.iloc[i] / 100.0)

    # Write back into the model (baseline arrays first)
    for i in range(n):
        t = i  # 0-based offset in DSA arrays
        model.rg_bl[t] = float(rg_bl.iloc[i])
        model.rgdp_bl[t] = float(rgdp_bl.iloc[i])
        model.rg_pot_bl[t] = float(rg_pot_bl.iloc[i])
        model.rgdp_pot_bl[t] = float(rgdp_pot_bl.iloc[i])
        model.output_gap_bl[t] = float(output_gap_bl.iloc[i])
        model.ng_bl[t] = float(ng_bl.iloc[i])
        model.ngdp_bl[t] = float(ngdp_bl.iloc[i])
        model.pi[t] = float(pi.iloc[i])

    # Keep current arrays consistent with baseline (project() will reset again)
    model.rg = model.rg_bl.copy()
    model.rgdp = model.rgdp_bl.copy()
    model.rg_pot = model.rg_pot_bl.copy()
    model.rgdp_pot = model.rgdp_pot_bl.copy()
    model.output_gap = model.output_gap_bl.copy()
    model.ng = model.ng_bl.copy()
    model.ngdp = model.ngdp_bl.copy()

    return model


def apply_selective_mtp_anchors_to_dsa(
    dsa_model,
    anchors: Dict[str, Union[pd.Series, Dict[int, float], Iterable[float]]],
    preserve_keys: list = None,
    inplace: bool = True,
) -> object:
    """
    Apply only selected MTP anchors to the DSA baseline.
    
    This function filters the provided anchors to only include the specified keys,
    then applies them using the existing apply_mtp_anchors_to_dsa function.
    
    Parameters:
        dsa_model: DSA model instance
        anchors: Dictionary of MTP anchors (same format as apply_mtp_anchors_to_dsa)
        preserve_keys: List of anchor keys to preserve (e.g., ['rg', 'pi'])
                       Default: ['rg', 'pi'] - preserve demand side only
        inplace: Whether to modify the provided dsa_model
    
    Returns: the modified dsa_model
    """
    if preserve_keys is None:
        preserve_keys = ['rg', 'pi']  # Default: preserve demand side only
    
    if not anchors:
        return dsa_model
    
    # Filter anchors to only include preserve_keys
    filtered_anchors = {k: v for k, v in anchors.items() if k in preserve_keys}
    
    if not filtered_anchors:
        return dsa_model
    
    # Apply filtered anchors using existing function
    return apply_mtp_anchors_to_dsa(dsa_model, anchors=filtered_anchors, inplace=inplace)


def _spb_steps_from_level_path(
    dsa_model,
    spb_bca_path: pd.Series,
) -> np.ndarray:
    """
    Convert an absolute SPB (before ageing, percent of GDP) path given by calendar years
    into DSA spb_steps array for the adjustment period length.
    """
    # Determine indices for adjustment period
    a0 = dsa_model.adjustment_start  # index in arrays
    a1 = dsa_model.adjustment_end
    years = np.arange(dsa_model.start_year, dsa_model.end_year + 1)
    # Get full array aligned to model years
    spb_full = spb_bca_path.reindex(years).to_numpy()
    # Steps are first differences from a0..a1
    steps = np.full((dsa_model.adjustment_period,), 0.0, dtype=float)
    for t in range(a0, a1 + 1):
        steps[t - a0] = spb_full[t] - spb_full[t - 1]
    return steps


def run_dsa_with_potential_and_spb(
    dsa_model,
    fs_df: Optional[pd.DataFrame] = None,
    spb_bca_path: Optional[pd.Series] = None,
    spb_steps: Optional[Iterable[float]] = None,
    post_spb_steps: Optional[Iterable[float]] = None,
    potential_start_year: Optional[int] = None,
    potential_end_year: Optional[int] = None,
    scenario: Optional[str] = None,
    mtp_anchors: Optional[Dict[str, Union[pd.Series, Dict[int, float], Iterable[float]]]] = None,
    *,
    use_growth_driven_preclosure: Optional[bool] = None,
):
    """
    Apply FS potential (optional) and a specified SPB path (levels or steps) to DSA,
    then run a projection.

    - If fs_df is provided, overwrite potential (rgdp_pot[_bl], rg_pot[_bl]) over the provided years.
    - Provide either spb_bca_path (absolute path by year) or spb_steps (differences) to DSA.
    - post_spb_steps can be used to guide periods after the adjustment window.
    """
    # Optionally apply MTP anchors (DSA_MTP baseline) BEFORE FS potential
    if mtp_anchors:
        apply_mtp_anchors_to_dsa(dsa_model, anchors=mtp_anchors, inplace=True)

    # Optionally apply potential
    if fs_df is not None:
        apply_fs_potential_to_dsa(
            dsa_model,
            fs_df=fs_df,
            start_year=potential_start_year,
            end_year=potential_end_year,
            inplace=True,
        )

    # Prepare steps
    steps_arr = None
    if spb_steps is not None:
        steps_arr = np.array(list(spb_steps), dtype=float)
    elif spb_bca_path is not None:
        if not isinstance(spb_bca_path, pd.Series):
            raise ValueError("spb_bca_path must be a pandas Series indexed by calendar years")
        steps_arr = _spb_steps_from_level_path(dsa_model, spb_bca_path)

    # EXPLICIT-ONLY LOGIC: Only change if user explicitly provided a value
    # Ensure default is False
    dsa_model.ensure_growth_driven_preclosure_default()
    
    # Save current flag to avoid side-effects across calls
    prev_flag = getattr(dsa_model, 'growth_driven_preclosure', False)
    
    try:
        # Only change if user explicitly provided a value
        if use_growth_driven_preclosure is not None:
            setattr(dsa_model, 'growth_driven_preclosure', bool(use_growth_driven_preclosure))
        else:
            # Default to False when no explicit value provided
            setattr(dsa_model, 'growth_driven_preclosure', False)
        
        # Run projection
        dsa_model.project(
            spb_steps=steps_arr,
            post_spb_steps=(np.array(list(post_spb_steps), dtype=float) if post_spb_steps is not None else None),
            scenario=scenario,
        )
    finally:
        # Restore original flag only if we changed it
        if use_growth_driven_preclosure is not None:
            setattr(dsa_model, 'growth_driven_preclosure', prev_flag)


def compare_binding_spb_under_potential(
    dsa_model,
    fs_df: pd.DataFrame,
    edp: bool = True,
    debt_safeguard: bool = True,
    deficit_resilience: bool = True,
    stochastic: bool = True,
    print_results: bool = False,
    *,
    use_growth_driven_preclosure: Optional[bool] = None,
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """
    Compare optimal/binding SPB under:
    - A: DSA-only (baseline potential)
    - B: DSA with adjusted potential from FS

    Returns:
    - summary DataFrame with key metrics and fiscal space differences
    - dictionary of time-series DataFrames for both cases
    """
    # Clone model for B
    model_A = copy.deepcopy(dsa_model)
    model_B = copy.deepcopy(dsa_model)

    # Case A: baseline potential
    model_A.find_spb_binding(
        edp=edp,
        debt_safeguard=debt_safeguard,
        deficit_resilience=deficit_resilience,
        stochastic=stochastic,
        print_results=print_results,
        save_df=True,
    )
    df_A = model_A.df_dict.get('binding', model_A.df(all=True))

    # Case B: apply FS potential then rerun binding
    apply_fs_potential_to_dsa(model_B, fs_df=fs_df, inplace=True)
    # Ensure default is False
    model_B.ensure_growth_driven_preclosure_default()
    
    # EXPLICIT-ONLY LOGIC: Only change if user explicitly provided a value
    if use_growth_driven_preclosure is not None:
        setattr(model_B, 'growth_driven_preclosure', use_growth_driven_preclosure)
    else:
        # Default to False when no explicit value provided
        setattr(model_B, 'growth_driven_preclosure', False)
    model_B.find_spb_binding(
        edp=edp,
        debt_safeguard=debt_safeguard,
        deficit_resilience=deficit_resilience,
        stochastic=stochastic,
        print_results=print_results,
        save_df=True,
    )
    df_B = model_B.df_dict.get('binding', model_B.df(all=True))

    # Extract SPB targets and steps
    spb_end_A = float(model_A.spb_target_dict.get('binding', np.nan))
    spb_end_B = float(model_B.spb_target_dict.get('binding', np.nan))
    steps_A = np.array(model_A.binding_parameter_dict['spb_steps'], dtype=float)
    steps_B = np.array(model_B.binding_parameter_dict['spb_steps'], dtype=float)

    # Build cumulative SPB (sum of steps)
    cum_A = np.cumsum(steps_A)
    cum_B = np.cumsum(steps_B)

    # Fiscal space delta (percent of GDP cumulative over adjustment window)
    # Positive delta means lower consolidation requirement under adjusted potential
    delta_cum_spb_pct = np.sum(steps_A - steps_B)

    # Convert to absolute amounts using NGDP over the adjustment window
    # Use model_B ngdp for amounts (close enough; could also take A)
    a0 = model_B.adjustment_start
    a1 = model_B.adjustment_end
    ngdp = model_B.ngdp[a0:a1 + 1]
    delta_amounts = (steps_A - steps_B) / 100.0 * ngdp
    delta_cum_spb_amt = float(np.sum(delta_amounts))

    summary = pd.DataFrame(
        {
            'spb_end_A': [spb_end_A],
            'spb_end_B': [spb_end_B],
            'delta_spb_end': [spb_end_B - spb_end_A],
            'cum_spb_pct_A': [float(np.sum(steps_A))],
            'cum_spb_pct_B': [float(np.sum(steps_B))],
            'delta_cum_spb_pct': [float(delta_cum_spb_pct)],
            'delta_cum_spb_amount': [delta_cum_spb_amt],
        }
    )

    timeseries = {
        'A_binding': df_A,
        'B_binding': df_B,
    }

    return summary, timeseries
