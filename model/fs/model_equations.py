"""
Model equations for the DZ Fiscal Sustainability Model.

This file contains all model blocks with their equations in Modelflow syntax.
"""

# =============================================================================
# SUPPLY BLOCK
# =============================================================================

SUPPLY_BLOCK = '''
£ --- Potential Output, Trend in logs ---                                          
Y_TREND = SR_TREND + 0.65 * L_TREND_LOG + 0.1 * K_G_LOG + 0.25 * K_M_LOG
Y_STAR = EXP(Y_TREND)

£ --- Potential Output Growth, real ---
G_Y_STAR = DIFF(Y_STAR) / Y_STAR(-1) * 100

£ --- log TFP ---  
SR_TREND = SR_TREND(-1) + SR_SLOPE(-1) + EPS_SR
<EXO> SR_SLOPE = (1 - RHO_SR) * OMEGA_SR + RHO_SR * SR_SLOPE(-1) + EPS_SR_SLOPE

£ --- Private Capital ---  
K_M = (1-DELTA_M) * K_M(-1) + I_M
K_M_LOG = LOG(K_M)
I_M = RHO_I_M * IQ_M/100 * Y_STAR + (1 - RHO_I_M) * (K_M(-1) * (Y_STAR / Y_STAR(-1) + DELTA_M - 1)) + EPS_I_M
IQ_M = PHI_IQ_M_0 + PHI_IQ_M_1 * IQ_M(-1) + PHI_IQ_M_2 * IQ_M(-2) - LAMBDA_IQ_M_1 * R_LT - LAMBDA_IQ_M_2 * TAU_F_STAR + LAMBDA_IQ_M_3 * S_SUB_STAR + LAMBDA_IQ_M_4 * Y_GAP  + EPS_IQ_M

£ --- Public Capital Accumulation ---  
£ --- I_G_REAL needed to be specified as "_REAL" to avoid confusion with I_G (all fiscal variables are in nominal terms) --- 
 
K_G = (1-DELTA_G) * K_G(-1) + THETA_KG_0 * I_G_REAL + (1-DELTA_G)*THETA_KG_1*I_G_REAL(-1) + (1-DELTA_G)**2*THETA_KG_2*I_G_REAL(-2) + (1-DELTA_G)**3*THETA_KG_3*I_G_REAL(-3) + (1-DELTA_G)**4*THETA_KG_4*I_G_REAL(-4) + (1-DELTA_G)**5*THETA_KG_5*I_G_REAL(-5) + (1-DELTA_G)**6*THETA_KG_6*I_G_REAL(-6) + (1-DELTA_G)**7*THETA_KG_7*I_G_REAL(-7) + (1-DELTA_G)**8*THETA_KG_8*I_G_REAL(-8) + (1-DELTA_G)**9*THETA_KG_9*I_G_REAL(-9) + (1-DELTA_G)**10 * THETA_KG_10 * I_G_REAL(-10)
K_G_LOG = LOG(K_G)

£ --- Labour ---  
L_TREND = WP * LP_TREND/100 * (1-U_TREND/100) * H_TREND
L_TREND_LOG = LOG(L_TREND)

£ --- Participation Rate ---  
LP_TREND = LP_TREND(-1) + LP_SLOPE(-1) + EPS_LP
<EXO> LP_SLOPE = RHO_LP * LP_SLOPE_AWG + (1 - RHO_LP)  * LP_SLOPE(-1) + EPS_LP_SLOPE

£ --- Unemployment Rate ---  
<EXO> U_TREND = U_TREND(-1) + U_SLOPE(-1) + EPS_U
<EXO> U_SLOPE = U_SLOPE(-1) + EPS_U_SLOPE

£ --- Average Hours Worked ---  
H_TREND = H_TREND(-1) + H_SLOPE(-1) + EPS_H
<EXO> H_SLOPE = RHO_H * H_SLOPE(-1) + EPS_H_SLOPE
'''



SUPPLY_BLOCK_NO_KG_LAG = '''
£ --- Potential Output, Trend in logs ---                                          
Y_TREND = SR_TREND + 0.65 * L_TREND_LOG + 0.1 * K_G_LOG + 0.25 * K_M_LOG
Y_STAR = EXP(Y_TREND)

£ --- Potential Output Growth, real ---
G_Y_STAR = DIFF(Y_STAR) / Y_STAR(-1) * 100

£ --- log TFP ---  
SR_TREND = SR_TREND(-1) + SR_SLOPE(-1) + EPS_SR
<EXO> SR_SLOPE = (1 - RHO_SR) * OMEGA_SR + RHO_SR * SR_SLOPE(-1) + EPS_SR_SLOPE

£ --- Private Capital ---  
K_M = (1-DELTA_M) * K_M(-1) + I_M
K_M_LOG = LOG(K_M)
I_M = RHO_I_M * IQ_M/100 * Y_STAR + (1 - RHO_I_M) * (K_M(-1) * (Y_STAR / Y_STAR(-1) + DELTA_M - 1)) + EPS_I_M
IQ_M = PHI_IQ_M_0 + PHI_IQ_M_1 * IQ_M(-1) + PHI_IQ_M_2 * IQ_M(-2) - LAMBDA_IQ_M_1 * R_LT - LAMBDA_IQ_M_2 * TAU_F_STAR + LAMBDA_IQ_M_3 * S_SUB_STAR + LAMBDA_IQ_M_4 * Y_GAP  + EPS_IQ_M

£ --- Public Capital Accumulation ---  
£ --- I_G_REAL needed to be specified as "_REAL" to avoid confusion with I_G (all fiscal variables are in nominal terms) --- 
 
K_G = (1-DELTA_G) * K_G(-1) + I_G_REAL 
K_G_LOG = LOG(K_G)

£ --- Labour ---  
L_TREND = WP * LP_TREND/100 * (1-U_TREND/100) * H_TREND
L_TREND_LOG = LOG(L_TREND)

£ --- Participation Rate ---  
LP_TREND = LP_TREND(-1) + LP_SLOPE(-1) + EPS_LP
<EXO> LP_SLOPE = RHO_LP * LP_SLOPE_AWG + (1 - RHO_LP)  * LP_SLOPE(-1) + EPS_LP_SLOPE

£ --- Unemployment Rate ---  
<EXO> U_TREND = U_TREND(-1) + U_SLOPE(-1) + EPS_U
<EXO> U_SLOPE = U_SLOPE(-1) + EPS_U_SLOPE

£ --- Average Hours Worked ---  
H_TREND = H_TREND(-1) + H_SLOPE(-1) + EPS_H
<EXO> H_SLOPE = RHO_H * H_SLOPE(-1) + EPS_H_SLOPE
'''


# =============================================================================
# DEMAND BLOCK
# =============================================================================

DEMAND_BLOCK = '''
£ --- GDP growth, log ---  
DIFF(Y_D_LOG) = DIFF(Y_TREND) - BETA_D * Y_GAP(-1) / 100 - LAMBDA_R * DIFF(I_LT) + LAMBDA_I_G * DIFF(LOG(I_G_REAL)) + LAMBDA_G * DIFF(LOG(G_REAL)) + LAMBDA_TR * DIFF(LOG(TR_REAL)) - LAMBDA_T_F * DIFF(LOG(T_F_REAL)) - LAMBDA_T_C * DIFF(LOG(T_C_REAL)) - LAMBDA_T_HH * DIFF(LOG(T_HH_REAL)) + EPS_Y_D

£ --- GDP, real ---  
Y_D = EXP(Y_D_LOG)

£ --- GDP growth, real ---  
G_Y_D = DIFF(Y_D) / Y_D(-1) * 100

£ --- Output gap ---  
Y_GAP = (Y_D - Y_STAR) / Y_STAR * 100
'''

# =============================================================================
# FISCAL BLOCK - PRIMARY BALANCE
# =============================================================================

FISCAL_BLOCK_PB = '''
£ --- All Fiscal Variables are in Nominal Terms, unless otherwise stated ---  

£ --- Primary Balance ---  
PB = GR - PE
PB_RATIO = PB / Y_D_NOM * 100

£ --- General Government Revenue ---  
GR = T_HH + T_F + T_C + SC_HH + SC_F + SC_IMP + NON_T

£ --- Taxes on Households ---  
T_HH = TAU_HH / 100 * Y_D_NOM
TAU_HH = TAU_HH_STAR + ALPHA_HH * Y_GAP + V_TAU_HH_STAR

£ --- Taxes on Firms ---  
T_F = TAU_F / 100 * Y_D_NOM
TAU_F = TAU_F_STAR + ALPHA_F * Y_GAP + V_TAU_F_STAR

£ --- Indirect Taxes (on Consumption) ---  
T_C = TAU_C / 100 * Y_D_NOM
TAU_C = TAU_C_STAR + ALPHA_C * Y_GAP + V_TAU_C_STAR

£ --- Social Security Contributions ---

£ --- SC from Households ---  
SC_HH = TAU_SC_HH / 100 * Y_D_NOM
TAU_SC_HH = TAU_SC_HH_STAR + ALPHA_SC_HH * Y_GAP + V_TAU_SC_HH_STAR

£ --- SC from Firms ---  
SC_F = TAU_SC_F / 100 * Y_D_NOM
TAU_SC_F = TAU_SC_F_STAR + ALPHA_SC_F * Y_GAP + V_TAU_SC_F_STAR

£ --- Imputed SC ---  
SC_IMP = TAU_SC_IMP / 100 * Y_D_NOM
TAU_SC_IMP = TAU_SC_IMP_STAR + ALPHA_SC_IMP * Y_GAP + V_TAU_SC_IMP_STAR

£ --- Other Revenue ---  
NON_T = TAU_NON_T / 100 * Y_D_NOM
TAU_NON_T = TAU_NON_T_STAR + ALPHA_NON_T * Y_GAP + V_TAU_NON_T_STAR

£ --- General Government Expenditure ---  
PE = G + I_G + SUB + TR + OTHER_PE

£ --- Government Consumption ---  
G = S_G / 100 * Y_D_NOM
S_G = S_G_STAR + ALPHA_G * Y_GAP + V_S_G_STAR

£ --- Government Investment ---  
I_G = S_IG / 100 * Y_D_NOM
S_IG = S_IG_STAR + ALPHA_IG * Y_GAP + V_S_IG_STAR

£ --- Subsidies ---  
SUB = S_SUB / 100 * Y_D_NOM
S_SUB = S_SUB_STAR + ALPHA_SUB * Y_GAP + V_S_SUB_STAR

£ --- Transfers ---  
TR = S_TR / 100 * Y_D_NOM
S_TR = S_TR_STAR + ALPHA_TR * Y_GAP + V_S_TR_STAR

£ --- Other Expenditure ---  
OTHER_PE = S_OTHER_PE / 100 * Y_D_NOM
S_OTHER_PE = S_OTHER_PE_STAR + ALPHA_OTHER_PE * Y_GAP + V_S_OTHER_PE_STAR
'''

# =============================================================================
# FISCAL BLOCK - DEBT DYNAMICS
# =============================================================================

FISCAL_BLOCK_DSA = '''
£ --- Debt Dynamics ---  

£ --- Debt ratio projection ---
D_RATIO = MAX(ALPHA_EUR * D_RATIO(-1) * (1 + IIR / 100) / (1 + G_Y_D_NOM / 100) + ALPHA_USD * D_RATIO(-1) * (1 + IIR / 100) / (1 + G_Y_D_NOM / 100) * DIFF(EXR_USD) - PB_RATIO + SF_RATIO, 0)

£ --- Nominal debt level ---
D = (D_RATIO / 100) * Y_D_NOM

£ --- Gross Financing Needs ---
GFN = INT + REP - PB + SF

£ --- Implicit interest rates ---
ALPHA_ST = D_ST / D
BETA_LT = D_LTN / D_LT

IIR_LT = BETA_LT(-1) * I_LT + (1 - BETA_LT(-1)) * IIR_LT(-1)
IIR = ALPHA_ST(-1) * I_ST + (1 - ALPHA_ST(-1)) * IIR_LT

£ --- Interest Payments ---
INT = IIR/100 * D(-1)
INTSHARE = INT / Y_D_NOM * 100

£ --- Repayments: Maturing ST and LT debt ---
REP_ST = D_ST(-1)
REP_LT = PHI_LT * D_LT(-1)
REP = REP_ST + REP_LT

£ --- Stock-Flow Adjustment: Exogenous constant share ---
SF = SF_RATIO / 100 * Y_D_NOM

£ --- Newly issued ST and LT debt: new and rolled-over debt ---
D_STN = MAX(0, GFN) * D_SHARE_ST
D_LTN = MAX(0, GFN) * (1 - D_SHARE_ST)

D_ST = D_STN + D_ST(-1) - REP_ST
D_LT = D_LTN + D_LT(-1) - REP_LT
'''

# =============================================================================
# FINANCIAL BLOCK
# =============================================================================

FINANCIAL_BLOCK = '''
£ --- SHORT-TERM POLICY RATE: TAYLOR RULE---
I_RATE = MAX(THETA_I * I_RATE(-1) + (1 - THETA_I) * (I_STAR + OMEGA_DE * (SIGMA_I_1 * (PI - PI_T) + SIGMA_I_2 * Y_GAP) + (1 - OMEGA_DE) * (SIGMA_I_1 * (PI_EA - PI_T) + SIGMA_I_2 * Y_GAP_EA)), I_LB)

£ --- DSA-ANCHORED SHORT-TERM INTEREST RATE ---
<EXO> I_ST = (1 - RHO_I) * I_RATE + RHO_I * I_ST_ANCHOR

£ --- DSA-ANCHORED LONG-TERM INTEREST RATE ---
DIFF(I_LT_RULE)   = DIFF(I_ST) + DIFF(TERM) + RISK + EPS_I
<EXO> I_LT = (1 - RHO_I) * (I_LT_RULE) + RHO_I * I_LT_ANCHOR

£ --- TERM PREMIUM AND FISCAL RISK ---
<EXO> TERM = THETA_TERM * TERM(-1) + (1 - THETA_TERM) * TERM_STAR
RISK = PHI_RISK * (DIFF(D_RATIO) * D_RATIO/D_RATIO_STAR)

£ --- Real interest rate ---
R_ST = I_ST - PI
R_LT = I_LT - PI
'''

# =============================================================================
# PRICES BLOCK
# =============================================================================

PRICES_BLOCK = '''
£ --- Inflation ---  
PI = BETA_PI_1 * PI(-1) + (1-BETA_PI_1) * PI_T + BETA_PI_2 * Y_GAP + EPS_PI

£ --- Price level ---
P = P(-1) * (1 + PI/100)

£ --- Nominal Values ---
Y_STAR_NOM = Y_STAR * P 
Y_D_NOM = Y_D * P 

£ --- Real Values for Government Revenue and Expenditure Items ---

T_HH_REAL = T_HH / P
T_F_REAL = T_F / P
T_C_REAL = T_C / P
SC_HH_REAL = SC_HH / P
SC_F_REAL = SC_F / P
SC_IMP_REAL = SC_IMP / P

G_REAL = G / P
I_G_REAL = I_G / P
SUB_REAL = SUB / P
TR_REAL = TR / P


G_Y_STAR_NOM = DIFF(Y_D_NOM) / Y_D_NOM(-1) * 100
G_Y_D_NOM = DIFF(Y_D_NOM) / Y_D_NOM(-1) * 100
'''

# =============================================================================
# COMPLETE MODEL
# =============================================================================

def build_model(include_fiscal=True, include_kg_lag=True):
    """
    Build the complete model from all blocks.
    
    Args:
        include_fiscal (bool): If True, includes fiscal blocks (FISCAL_BLOCK_PB and FISCAL_BLOCK_DSA).
                              If False, excludes fiscal blocks for supply/demand only analysis.
        include_kg_lag (bool): If True, includes the lag in the public capital accumulation equation.
                              If False, excludes the lag.
    Returns:
        model: ModelClass model object
    """
    from modelclass import model
    
    # Core blocks that are always included
    if include_kg_lag:
        core_blocks = SUPPLY_BLOCK + DEMAND_BLOCK + FINANCIAL_BLOCK + PRICES_BLOCK
    else:
        core_blocks = SUPPLY_BLOCK_NO_KG_LAG + DEMAND_BLOCK + FINANCIAL_BLOCK + PRICES_BLOCK
    
    # Add fiscal blocks if requested
    if include_fiscal:
        complete_model = core_blocks + FISCAL_BLOCK_PB + FISCAL_BLOCK_DSA
    else:
        complete_model = core_blocks
    
    return model.from_eq(complete_model)

def build_core_model():
    """
    Build the core model without fiscal blocks (supply, demand, financial, and prices only).
    
    This is equivalent to calling build_model(include_fiscal=False, include_kg_lag=True).
    Useful for analyzing supply/demand dynamics without fiscal policy effects.
    
    Returns:
        model: ModelClass model object with core blocks only
    """
    return build_model(include_fiscal=False, include_kg_lag=True)

# =============================================================================
# MODEL DOCUMENTATION
# =============================================================================

MODEL_DESCRIPTION = """
DZ Fiscal Sustainability Model

This model combines elements from:
- OECD Fiscal Maquette Model (fiscal policy framework)
- EUCAM framework (supply side and labor market)
- DSA methodology (debt sustainability analysis)

Key Features:
1. Semi-structural approach with behavioral equations
2. Detailed fiscal block with revenue/expenditure components
3. DSA-compliant debt dynamics
4. EUCAM-consistent labor market modeling
5. Flexible scenario analysis capabilities
6. Optional fiscal block exclusion for core analysis

Model Blocks:
- Supply: Potential output, capital, labor market
- Demand: GDP growth, fiscal multipliers, output gap
- Fiscal: Government finances, debt dynamics (optional)
- Financial: Interest rates, monetary policy
- Prices: Inflation, nominal values

Usage:
- build_model(): Full model with all blocks (default)
- build_model(include_fiscal=False, include_kg_lag=False): Core model without fiscal blocks and without the lag in the public capital accumulation equation
- build_core_model(): Convenience function for non-fiscal analysis
"""
