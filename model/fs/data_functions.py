"""
Data loading and processing functions for the DZ Fiscal Sustainability Model.

This file handles data loading, parameter calculations, and data preprocessing.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from debug_utils import (
    debug_print, debug_print_search, debug_print_success, 
    debug_print_error, debug_print_info, debug_print_warning
)

# =============================================================================
# DATA LOADING
# =============================================================================

def load_data(data_folder="02_Daten", sheet_name="Germany"):
    """
    Load main data files for the model.
    
    Parameters:
        data_folder: str, path to data directory
        sheet_name: str, name of the sheet to load (default: "Germany")
        
    Returns:
        pd.DataFrame: loaded and processed data
    """
    # Get the absolute path to the project root
    # This file is in 03_Modell/FS_Model/, so we go up two levels to get to project root
    project_root = Path(__file__).parent.parent.parent
    
    # Handle data folder path - if it's a relative path, resolve it relative to project root
    if os.path.isabs(data_folder):
        data_folder_path = Path(data_folder)
    else:
        # If relative path, resolve it relative to project root
        data_folder_path = project_root / data_folder
    
    # Define file paths
    main_filename = "Data_Parameters_FS Model.xlsx"
    lt_growth_filename = "LT growth rates.xlsx"
    
    main_filepath = data_folder_path / main_filename
    lt_growth_filepath = data_folder_path / lt_growth_filename
    
    # Debug information
    debug_print_info("Project root", str(project_root))
    debug_print_info("Data folder path", str(data_folder_path))
    debug_print_info("Main file path", str(main_filepath))
    debug_print_info("File exists", str(main_filepath.exists()))
    
    # Load main data with specified sheet name
    data = pd.read_excel(main_filepath, sheet_name=sheet_name, index_col=0)
    
    # Ensure index is in integers (years)
    data.index = data.index.astype(int)
    
    # Load LT growth rates data (single sheet) - COMMENTED OUT
    # try:
    #     lt_growth_data = pd.read_excel(lt_growth_filepath, sheet_name="Growth", index_col=0)
    #     print(f"✓ Successfully loaded LT growth rates data")
    #     
    # except FileNotFoundError:
    #     print(f"⚠️  LT growth rates file not found: {lt_growth_filepath}")
    #     lt_growth_data = None
    # except Exception as e:
    #     print(f"⚠️  Error loading LT growth rates data: {e}")
    #     lt_growth_data = None
    
    # Set lt_growth_data to None since we're not loading it
    lt_growth_data = None
    
    return data, lt_growth_data

def load_parameters_from_excel(data_folder=None, country_code="DE"):
    """
    Load estimated parameters from country-specific Excel file.
    
    Parameters:
        data_folder: str, path to data directory (if None, will auto-detect)
        country_code: str, country code (e.g., "DE", "FR", "IT")
        
    Returns:
        dict: dictionary containing all parameter sections
    """
    try:
        # ALWAYS look in the Estimation folder first (where the estimation just saved the file)
        estimation_folder = Path(__file__).parent / "estimation"
        estimation_filepath = estimation_folder / f"estimated_parameters_{country_code}.xlsx"
        
        debug_print_search(f"Looking for parameter file for country", country_code)
        debug_print_info("Estimation folder", estimation_folder)
        debug_print_info("Full file path", estimation_filepath)
        
        # List all available parameter files in the Estimation folder
        available_files = list(estimation_folder.glob("estimated_parameters_*.xlsx"))
        if available_files:
            debug_print_search("Available parameter files in Estimation folder", "")
            for file in available_files:
                debug_print(f"    {file.name}")
        else:
            debug_print_search("No parameter files found in Estimation folder", "")
        
        if estimation_filepath.exists():
            debug_print_success(f"Found parameter file in Estimation folder: {estimation_filepath}")
            filepath = estimation_filepath
        else:
            debug_print_error(f"Parameter file NOT found in Estimation folder!")
            debug_print_info("Expected file", f"estimated_parameters_{country_code}.xlsx")
            debug_print_info("Searched in", estimation_folder)
            debug_print_info("Current working directory", Path.cwd())
            debug_print_info("__file__ location", __file__)
            return None
        
        # Load all sheets
        excel_file = pd.ExcelFile(filepath)
        loaded_params = {}
        
        for sheet_name in excel_file.sheet_names:
            if sheet_name != 'Metadata':
                df = pd.read_excel(filepath, sheet_name=sheet_name)
                if not df.empty and 'Parameter' in df.columns and 'Estimated_Value' in df.columns:
                    loaded_params[sheet_name] = dict(zip(df['Parameter'], df['Estimated_Value']))
        
        if loaded_params:
            debug_print_success(f"Parameters loaded from estimated_parameters_{country_code}.xlsx")
            debug_print_info("Sections found", list(loaded_params.keys()))
            for section, params in loaded_params.items():
                debug_print_info(f"{section}", f"{len(params)} parameters")
                for param, value in params.items():
                    debug_print(f"      {param}: {value}")
            return loaded_params
        else:
            debug_print_error("No valid parameter data found in file")
            return None
            
    except Exception as e:
        debug_print_error(f"Error loading parameters: {str(e)}")
        return None

def get_data_folder_path():
    """
    Get the correct path to the data folder from common working directory locations.
    
    Returns:
        str: Path to the 02_Daten folder
    """
    current_dir = Path.cwd()
    
    # Try different relative paths based on common working directory locations
    possible_paths = [
        "02_Daten",                    # If in project root
        "../02_Daten",                 # If in 03_Modell
        "../../02_Daten",              # If in 03_Modell/subfolder
        "../03_Modell/02_Daten",       # If in 02_Daten
        "03_Modell/02_Daten",          # If in project root
    ]
    
    for path in possible_paths:
        test_path = current_dir / path
        if test_path.exists():
            return str(test_path)
    
    # If none found, return the default
    return "02_Daten"

def get_parameter_value(parameters, section, param_name, default_value=None):
    """
    Get a parameter value from the loaded parameters with fallback to default.
    
    Parameters:
        parameters: dict, loaded parameters from load_parameters_from_excel
        section: str, parameter section (e.g., 'demand', 'investment', 'inflation', 'tfp')
        param_name: str, parameter name
        default_value: any, default value if parameter not found
        
    Returns:
        any: parameter value or default value
    """
    try:
        if parameters and section in parameters and param_name in parameters[section]:
            return parameters[section][param_name]
        else:
            if default_value is not None:
                debug_print_warning(f"Parameter {section}.{param_name} not found, using default: {default_value}")
                return default_value
            else:
                debug_print_error(f"Parameter {section}.{param_name} not found and no default provided")
                return None
    except Exception as e:
        debug_print_error(f"Error accessing parameter {section}.{param_name}: {str(e)}")
        return default_value

# =============================================================================
# SUPPLY BLOCK CALCULATIONS
# =============================================================================

def calculate_supply_variables(data):
    """Calculate supply block variables and parameters."""
    
    # Calculate the log of potential output (Y_TREND)
    data.loc[:, "Y_TREND"] = np.log(data.loc[:, "Y_STAR"])
    
    # Calculate nominal potential output
    data.loc[:, "Y_STAR_NOM"] = data.loc[:, "Y_STAR"] * data.loc[:, "P"]
    
    # Calculate growth rate of potential output (in percent)
    data.loc[:, "G_Y_STAR"] = data.loc[:, "Y_STAR"].diff() / data.loc[:, "Y_STAR"].shift(1) * 100
    
    # Set weights for short-term versus long-term investment rule
    # Phase 1: Short-term rule (2025-2029) - weight = 1
    data.loc[2025:2029, 'RHO_I_M'] = 1
    
    # Phase 2: Convergence (2030-2039) - linear decrease from 1 to 0
    convergence_years = range(2030, 2040)
    n_years = len(convergence_years)
    for i, year in enumerate(convergence_years):
        weight = 1 - (i / (n_years - 1))
        data.loc[year, 'RHO_I_M'] = weight
    
    # Phase 3: Long-term rule (2040 onwards) - weight = 0
    data.loc[2040:, 'RHO_I_M'] = 0
    
    # Set lag structure for public capital (THETA_KG_i) for i=0 to 10
    theta_values = [0, 0.2, 0.2, 0.15, 0.1, 0.075, 0.075, 0.05, 0.05, 0.05, 0.05]
    for i, theta in enumerate(theta_values):
        data.loc[:, f"THETA_KG_{i}"] = theta
    
    # Calculate LP_SLOPE_AWG
    data.loc[:, "LP_SLOPE_AWG"] = data.loc[:, "LP_AWG"].diff().shift(-1)
    
    # Set RHO_H equal to 1
    data.loc[:, "RHO_H"] = 1
    
    # Simple unemployment convergence: interpolate U_TREND_EUCAM to STRUCT_U_EUCAM
    u_trend_last_year = int(data.loc[:, "U_TREND_EUCAM"].dropna().index.max())
    struct_u_last_year = int(data.loc[:, "STRUCT_U_EUCAM"].dropna().index.max())
    years = list(range(u_trend_last_year, struct_u_last_year + 1))
    interpolated = pd.Series(
        np.linspace(data.loc[u_trend_last_year, "U_TREND_EUCAM"], 
                   data.loc[struct_u_last_year, "STRUCT_U_EUCAM"], len(years)),
        index=years
    )
    data.loc[years, "U_TREND_EUCAM"] = interpolated
    data.loc[data.index > struct_u_last_year, "U_TREND_EUCAM"] = data.loc[struct_u_last_year, "STRUCT_U_EUCAM"]
    
    # Calculate trend labor input (using EUCAM values)
    data.loc[:, "L_TREND"] = (
        data.loc[:, "WP"] * data.loc[:, "LP_TREND_EUCAM"]/100 * 
        (1-data.loc[:, "U_TREND_EUCAM"]/100) * data.loc[:, "H_TREND_EUCAM"]
    )

    # Calculate TFP trend (using EUCAM values)
    data.loc[:, "SR_TREND_EUCAM"] = (
        np.log(data.loc[:, "Y_STAR"]) -
        0.65 * np.log(data.loc[:, "L_TREND"]) -
        0.1 * np.log(data.loc[:, "K_G"]) -
        0.25 * np.log(data.loc[:, "K_M"])
    )

    # Calculate slope variables for EUCAM estimates
    eucam_trend_cols = ["SR_TREND_EUCAM", "LP_TREND_EUCAM", "U_TREND_EUCAM", "H_TREND_EUCAM"]
    eucam_slope_names = ["SR_SLOPE_EUCAM", "LP_SLOPE_EUCAM", "U_SLOPE_EUCAM", "H_SLOPE_EUCAM"]
    
    # Calculate slopes one by one, then shift back one year
    for trend_col, slope_col in zip(eucam_trend_cols, eucam_slope_names):
        data.loc[:, slope_col] = data.loc[:, trend_col].diff()
        data.loc[:, slope_col] = data.loc[:, slope_col].shift(-1)
    
    # Log of trend labor input
    data.loc[:, "L_TREND_LOG"] = np.log(data.loc[:, "L_TREND"])
    
    # Log of market and government capital
    data.loc[:, "K_M_LOG"] = np.log(data.loc[:, "K_M"])
    data.loc[:, "K_G_LOG"] = np.log(data.loc[:, "K_G"])
    
    return data

# =============================================================================
# DEMAND BLOCK CALCULATIONS
# =============================================================================

def calculate_demand_variables(data):
    """Calculate demand block variables."""
    
    # Calculate the log of (demand-side) GDP
    data.loc[:, "Y_D_LOG"] = np.log(data.loc[:, "Y_D"])
    
    # Calculate growth rate of (demand-side) GDP (in percent)
    data.loc[:, "G_Y_D"] = data.loc[:, "Y_D"].diff() / data.loc[:, "Y_D"].shift(1) * 100
    
    return data

# =============================================================================
# PRICES BLOCK CALCULATIONS
# =============================================================================

def calculate_price_variables(data):
    """Calculate price and nominal variables."""
    
    # Calculate nominal growth rates for potential output and GDP
    data.loc[:, "G_Y_STAR_NOM"] = data.loc[:,"Y_STAR_NOM"].diff() / data.loc[:, "Y_STAR_NOM"].shift(1) * 100
    data.loc[:, "G_Y_D_NOM"] = data.loc[:,"Y_D_NOM"].diff() / data.loc[:, "Y_D_NOM"].shift(1) * 100
    
    # Calculate real government expenditure and revenue items
    # Revenue items (real)
    data.loc[:, "T_HH_REAL"] = data.loc[:, "T_HH"] / data.loc[:, "P"]
    data.loc[:, "T_F_REAL"] = data.loc[:, "T_F"] / data.loc[:, "P"]
    data.loc[:, "T_C_REAL"] = data.loc[:, "T_C"] / data.loc[:, "P"]
    data.loc[:, "SC_HH_REAL"] = data.loc[:, "SC_HH"] / data.loc[:, "P"]
    data.loc[:, "SC_F_REAL"] = data.loc[:, "SC_F"] / data.loc[:, "P"]
    data.loc[:, "SC_IMP_REAL"] = data.loc[:, "SC_IMP"] / data.loc[:, "P"]
    
    # Expenditure items (real)
    data.loc[:, "G_REAL"] = data.loc[:, "G"] / data.loc[:, "P"]
    data.loc[:, "I_G_REAL"] = data.loc[:, "I_G"] / data.loc[:, "P"]
    data.loc[:, "SUB_REAL"] = data.loc[:, "SUB"] / data.loc[:, "P"]
    data.loc[:, "TR_REAL"] = data.loc[:, "TR"] / data.loc[:, "P"]
    
    # Calculate logarithms of real government expenditure and revenue items
    # Log of real revenue items
    data.loc[:, "LOG_T_HH_REAL"] = np.log(data.loc[:, "T_HH_REAL"])
    data.loc[:, "LOG_T_F_REAL"] = np.log(data.loc[:, "T_F_REAL"])
    data.loc[:, "LOG_T_C_REAL"] = np.log(data.loc[:, "T_C_REAL"])
    
    # Log of real expenditure items
    data.loc[:, "LOG_G_REAL"] = np.log(data.loc[:, "G_REAL"])
    data.loc[:, "LOG_I_G_REAL"] = np.log(data.loc[:, "I_G_REAL"])
    data.loc[:, "LOG_SUB_REAL"] = np.log(data.loc[:, "SUB_REAL"])
    data.loc[:, "LOG_TR_REAL"] = np.log(data.loc[:, "TR_REAL"])
    
    return data

# =============================================================================
# FINANCIAL BLOCK CALCULATIONS
# =============================================================================

def calculate_financial_variables(data):
    """Calculate financial block variables and parameters."""
    
    # Set short-term interest rate 
    data.loc[:, "I_ST"] = data["I_RATE"]
    
    # Set up I_ST_ANCHOR and I_LT_ANCHOR: linear interpolation
    years = np.arange(2024, 2055)
    years_in_index = [year for year in years if year in data.index]
    
    if len(years_in_index) > 0:
        # Interpolate for all years in the range
        i_st_anchor_interp = np.interp(
            years_in_index,
            [2024, 2034, 2054],
            [data.loc[2024, "I_ST"], data.loc[2034, "I_ST_10F"], 2.0]
        )
        i_lt_anchor_interp = np.interp(
            years_in_index,
            [2024, 2034, 2054],
            [data.loc[2024, "I_LT"], data.loc[2034, "I_LT_10F"], 4.0]
        )
        data.loc[years_in_index, "I_ST_ANCHOR"] = i_st_anchor_interp
        data.loc[years_in_index, "I_LT_ANCHOR"] = i_lt_anchor_interp
    
    # Calculate OMEGA_DE: Germany's share of EA GDP
    data.loc[:, "OMEGA_DE"] = data.loc[:, "Y_D"] / data.loc[:, "GDP_EA"]
    data.loc[2024:, "OMEGA_DE"] = data.loc[2024:, "OMEGA_DE"].ffill()
    
    # Calculate the neutral interest rate (I_STAR)
    data.loc[:, "I_STAR"] = (
        (data.loc[:, "I_RATE"] - data.loc[:, "THETA_I"] * data.loc[:, "I_RATE"].shift(1))
        / (1 - data.loc[:, "THETA_I"])
        - data.loc[:, "OMEGA_DE"] * (
            data.loc[:, "SIGMA_I_1"] * (data.loc[:, "PI"] - data.loc[:, "PI_T"])
            + data.loc[:, "SIGMA_I_2"] * data.loc[:, "Y_GAP"]
        )
        - (1 - data.loc[:, "OMEGA_DE"]) * (
            data.loc[:, "SIGMA_I_1"] * (data.loc[:, "PI_EA"] - data.loc[:, "PI_T"])
            + data.loc[:, "SIGMA_I_2"] * data.loc[:, "Y_GAP_EA"]
        )
    )
    data.loc[2024:, "I_STAR"] = data.loc[2024:, "I_STAR"].ffill()
    
    # Override I_STAR for years 2025 and after
    data.loc[2025:, "I_STAR"] = 2.5
    
    # Set up helper variable for I_LT_RULE
    data.loc[:, "I_LT_RULE"] = data.loc[:, "I_LT"]
    
    # Calculate the term spread (long minus short rate)
    data.loc[:, "TERM"] = data["I_LT"] - data["I_ST"]
    
    # Calculate TERM_STAR: average term spread from 1999 to 2014
    term_star_years = data.loc[1999:2014, "TERM"].dropna()
    term_star_value = term_star_years.mean()
    data.loc[:, "TERM_STAR"] = term_star_value
    
    # Calculate risk premium
    data.loc[:, "RISK"] = data.loc[:, "PHI_RISK"] * data.loc[:, "D_RATIO"] / data.loc[:, "D_RATIO_STAR"]
    
    # Calculate real short and long rates
    data.loc[:, "R_ST"] = data["I_ST"] - data["PI"]
    data.loc[:, "R_LT"] = data["I_LT"] - data["PI"]
    
    # Calculate RHO_I values for DSA-anchored interest rate method (logistic transition from endogenous to anchored)
    # This creates a smooth transition where:
    # - Early years (2025-2030): RHO_I ≈ 0 → mostly endogenous interest rates
    # - Transition period (2030-2035): RHO_I gradually increases
    # - Later years (2035+): RHO_I ≈ 1 → fully anchored to DSA projections
    k = 0.65
    t0 = 6
    start_year = 2025
    end_year = 2045
    
    # Calculate years range for RHO_I calculations
    years = np.arange(start_year - 1, end_year + 1)
    years_in_data = [year for year in years if year in data.index]
    
    # Calculate logistic function for rho values
    t = np.array(years_in_data) - (start_year - 1)
    
    def rho_logistic(tt, k=k, t0=t0):
        return 1 / (1 + np.exp(-k * (tt - t0)))
    
    rho_values = rho_logistic(t)
    rho_series = pd.Series(rho_values, index=years_in_data)
    data.loc[years_in_data, "RHO_I_VALUES"] = rho_series.values
    
    # Set RHO_I_VALUES to 0 for years before start_year and 1 for years after end_year
    data.loc[data.index < start_year, "RHO_I_VALUES"] = 0
    data.loc[data.index > end_year, "RHO_I_VALUES"] = 1
    
    return data

# =============================================================================
# FISCAL BLOCK CALCULATIONS
# =============================================================================

def calculate_fiscal_variables(data):
    """Calculate fiscal block variables and parameters."""
    
    # Calculate revenue and expenditure shares as percent of nominal GDP
    # Expenditure shares
    data.loc[:, "S_IG"] = data.loc[:, "I_G"] / data.loc[:, "Y_D_NOM"] * 100
    data.loc[:, "S_G"] = data.loc[:, "G"] / data.loc[:, "Y_D_NOM"] * 100
    data.loc[:, "S_SUB"] = data.loc[:, "SUB"] / data.loc[:, "Y_D_NOM"] * 100
    data.loc[:, "S_TR"] = data.loc[:, "TR"] / data.loc[:, "Y_D_NOM"] * 100
    
    # Revenue shares
    data.loc[:, "TAU_HH"] = data.loc[:, "T_HH"] / data.loc[:, "Y_D_NOM"] * 100
    data.loc[:, "TAU_F"] = data.loc[:, "T_F"] / data.loc[:, "Y_D_NOM"] * 100
    data.loc[:, "TAU_C"] = data.loc[:, "T_C"] / data.loc[:, "Y_D_NOM"] * 100
    data.loc[:, "TAU_SC_HH"] = data.loc[:, "SC_HH"] / data.loc[:, "Y_D_NOM"] * 100
    data.loc[:, "TAU_SC_F"] = data.loc[:, "SC_F"] / data.loc[:, "Y_D_NOM"] * 100
    data.loc[:, "TAU_SC_IMP"] = data.loc[:, "SC_IMP"] / data.loc[:, "Y_D_NOM"] * 100
    
    # Calculate share of short-term debt
    data.loc[:, "ALPHA_ST"] = data.loc[:, "D_ST"] / data.loc[:, "D"]
    
    # Calculate D_SHARE_ST as constant from 2024 onwards
    d_share_st_const = data.loc[:, "ALPHA_ST"].dropna().tail(3).mean()
    data.loc[2024:, "D_SHARE_ST"] = d_share_st_const
    
    # Calculate implicit interest rate on long-term debt
    data.loc[:, "IIR_LT"] = (
        data.loc[:, "IIR"] - data.loc[:, "ALPHA_ST"].shift(1) * data.loc[:, "I_ST"]
    ) / (1 - data.loc[:, "ALPHA_ST"].shift(1))
    
    # Calculate repayments: short-term and long-term
    data.loc[:, "REP_ST"] = data.loc[:, "D_ST"].shift(1)
    data.loc[:, "REP_LT"] = data.loc[:, "D_residual_maturity_ST"].shift(1) - data.loc[:, "D_ST"].shift(1)
    data.loc[:, "REP"] = data.loc[:, "REP_ST"] + data.loc[:, "REP_LT"]
    
    # Calculate new short-term and long-term debt
    data.loc[:, "D_STN"] = data.loc[:, "D_ST"]
    data.loc[:, "D_LTN"] = data.loc[:, "D_LT"] - data.loc[:, "D_LT"].shift(1) + data.loc[:, "REP_LT"]
    
    # Calculate share of new long-term debt
    data.loc[:, "BETA_LT"] = data.loc[:, "D_LTN"] / data.loc[:, "D_LT"]
    
    # Calculate PHI_LT (repayment ratio for long-term debt)
    phi_lt = calculate_phi_lt(data)
    data.loc[:, "PHI_LT"] = phi_lt
    
    # Calculate stock-flow adjustment ratio
    data.loc[:, "SF_RATIO"] = data.loc[:, "SF"] / data.loc[:, "Y_D_NOM"] * 100
    data.loc[2027:, "SF_RATIO"] = 0
    
    # Calculate gross financing needs
    data.loc[:, "GFN"] = data.loc[:, "INT"] + data.loc[:, "REP"] + data.loc[:, "SF"] - data.loc[:, "PB"]
    
    return data

def calculate_phi_lt(data):
    """Calculate PHI_LT (repayment ratio for long-term debt)."""
    
    phi_lt = pd.Series(index=data.index, dtype=float)
    
    # For years up to and including 2025
    phi_lt.loc[:2025] = data.loc[:2025, "REP_LT"] / data.loc[:2025, "D_LT"].shift(1)
    
    # Calculate 6-year historical average (2020-2025)
    phi_lt_hist_avg = phi_lt.loc[2020:2025].mean()
    
    # For 2026-2035: linearly interpolate from 2025 to historical average
    years_interp = data.index[(data.index >= 2026) & (data.index <= 2035)]
    if len(years_interp):
        start_val = phi_lt.loc[2025]
        phi_lt.loc[years_interp] = np.linspace(start_val, phi_lt_hist_avg, len(years_interp)+1)[1:]
    
    # For 2036-2045: set to historical average
    years_constant = data.index[(data.index >= 2036) & (data.index <= 2045)]
    phi_lt.loc[years_constant] = phi_lt_hist_avg
    
    return phi_lt

# =============================================================================
# PRODUCTION FUNCTION VARIABLES
# =============================================================================

def calculate_production_variables(data):
    """Calculate additional variables for production function."""
    
    # Note: Most production function variables are now calculated in calculate_supply_variables
    # This function is kept for any future production-specific calculations
    
    return data

# =============================================================================
# MAIN DATA PROCESSING FUNCTION
# =============================================================================

def process_data(data):
    """
    Process all data and calculate required variables.
    
    Parameters:
        data: pd.DataFrame, raw data from Excel
        
    Returns:
        pd.DataFrame: processed data with all calculated variables
    """
    
    # Process each block
    data = calculate_supply_variables(data)
    data = calculate_demand_variables(data)
    data = calculate_price_variables(data)
    data = calculate_financial_variables(data)
    data = calculate_fiscal_variables(data)
    data = calculate_production_variables(data)
    
    return data

def load_and_process_data(data_folder="02_Daten", sheet_name="Germany"):
    """
    Load and process all data for the model.
    
    Parameters:
        data_folder: str, path to data directory
        sheet_name: str, name of the sheet to load (default: "Germany")
        
    Returns:
        pd.DataFrame: processed data with all calculated variables
    """
    
    # Load raw data with specified sheet name
    data, lt_growth_data = load_data(data_folder, sheet_name)
    
    # Note: lt_growth_data is not used (commented out in load_data)
    # lt_growth_data is set to None in load_data function
    
    # Process data
    processed_data = process_data(data)
    
    # Load and apply estimated parameters from Excel file
    # Extract country code from sheet name
    country_code = sheet_name.upper() if sheet_name.upper() in ['DE', 'AT', 'FI', 'FR', 'IT', 'NL'] else 'DE'
    
    excel_params = load_parameters_from_excel(country_code=country_code)
    if excel_params:
        debug_print_success(f"Assigning estimated parameters from Excel file for {country_code}...")
        # Demand parameters (fiscal multipliers)
        processed_data['BETA_D'] = get_parameter_value(excel_params, 'demand', 'beta_D', processed_data['BETA_D'].iloc[0])
        processed_data['LAMBDA_R'] = get_parameter_value(excel_params, 'demand', 'lambda_r', processed_data['LAMBDA_R'].iloc[0])
        processed_data['LAMBDA_I_G'] = get_parameter_value(excel_params, 'demand', 'lambda_ig', processed_data['LAMBDA_I_G'].iloc[0])
        processed_data['LAMBDA_G'] = get_parameter_value(excel_params, 'demand', 'lambda_g', processed_data['LAMBDA_G'].iloc[0])
        processed_data['LAMBDA_TR'] = get_parameter_value(excel_params, 'demand', 'lambda_tr', processed_data['LAMBDA_TR'].iloc[0])
        processed_data['LAMBDA_T_HH'] = get_parameter_value(excel_params, 'demand', 'lambda_t_hh', processed_data['LAMBDA_T_HH'].iloc[0])
        processed_data['LAMBDA_T_F'] = get_parameter_value(excel_params, 'demand', 'lambda_t_f', processed_data['LAMBDA_T_F'].iloc[0])
        processed_data['LAMBDA_T_C'] = get_parameter_value(excel_params, 'demand', 'lambda_t_c', processed_data['LAMBDA_T_C'].iloc[0])
        # Investment parameters
        processed_data['PHI_IQ_M_0'] = get_parameter_value(excel_params, 'investment', 'PHI_IQ_M_0', processed_data['PHI_IQ_M_0'].iloc[0])
        processed_data['PHI_IQ_M_1'] = get_parameter_value(excel_params, 'investment', 'PHI_IQ_M_1', processed_data['PHI_IQ_M_1'].iloc[0])
        processed_data['PHI_IQ_M_2'] = get_parameter_value(excel_params, 'investment', 'PHI_IQ_M_2', processed_data['PHI_IQ_M_2'].iloc[0])
        processed_data['LAMBDA_IQ_M_1'] = get_parameter_value(excel_params, 'investment', 'lambda_iq_m_1', processed_data['LAMBDA_IQ_M_1'].iloc[0])
        processed_data['LAMBDA_IQ_M_2'] = get_parameter_value(excel_params, 'investment', 'lambda_iq_m_2', processed_data['LAMBDA_IQ_M_2'].iloc[0])
        processed_data['LAMBDA_IQ_M_3'] = get_parameter_value(excel_params, 'investment', 'lambda_iq_m_3', processed_data['LAMBDA_IQ_M_3'].iloc[0])
        processed_data['LAMBDA_IQ_M_4'] = get_parameter_value(excel_params, 'investment', 'lambda_iq_m_5', processed_data['LAMBDA_IQ_M_4'].iloc[0])
        # Inflation parameters (Phillips curve)
        processed_data['BETA_PI_1'] = get_parameter_value(excel_params, 'inflation', 'beta', processed_data['BETA_PI_1'].iloc[0])
        processed_data['BETA_PI_2'] = get_parameter_value(excel_params, 'inflation', 'gamma', processed_data['BETA_PI_2'].iloc[0])
        # TFP parameters (trend components)
        processed_data['OMEGA_SR'] = get_parameter_value(excel_params, 'tfp', 'omega_sr', processed_data['OMEGA_SR'].iloc[0])
        processed_data['RHO_SR'] = get_parameter_value(excel_params, 'tfp', 'rho_sr', processed_data['RHO_SR'].iloc[0])
        debug_print_success(f"✓ Parameters loaded from Excel file and assigned to {country_code}")
    else:
        debug_print_warning(f"⚠️  Could not load parameters from Excel for {country_code}, using default values")
    
    return processed_data
