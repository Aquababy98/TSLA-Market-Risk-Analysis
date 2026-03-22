"""
PROJECT: TSLA Market Risk & Volatility Monitor
PURPOSE: Automates the collection of stock data to identify 'Safety Cushion' 
         thresholds and categorize market movement into risk clusters.
AUTHOR: Oceana O'Dean
DATE: March 2026
"""

import yfinance as yf
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
TICKER = "TSLA"
PERIOD = "1mo"  # Can be adjusted to '5d' for short-term snapshots
INTERVAL = "1h" # Hourly data provides the best balance for volatility analysis

print(f"Fetching live data for {TICKER}... ")

# Data Acquisition via yfinance API
data = yf.download(TICKER, period=PERIOD, interval=INTERVAL)

# Flattening multi-index columns for easier Excel processing
data.columns = data.columns.get_level_values(0)

# --- ANALYTICAL LOGIC ---

# 1. Smoothing Market Noise:
# Using a 5-hour rolling average to establish a 'Normal Price' baseline.
# This prevents overreacting to minor hourly price spikes.
data['Normal_Price'] = data['Close'].rolling(window=5).mean()

def check_risk(row):
    """
    Evaluates the 'Safety Cushion'—the distance between the current price 
    and the 2% statistical danger zone.
    """
    current_close = float(row['Close'])
    normal_avg = float(row['Normal_Price'])
    
    # Handling the initial window where the rolling average isn't yet calculated
    if pd.isna(normal_avg):
        return 'Initializing...', 0
    
    # 2. Risk Threshold Calculation:
    # We define the 'Danger Line' as 2% below the moving average.
    danger_line = normal_avg * 0.98
    
    # Calculating the gap (Cushion) between current price and the danger line
    cushion = (current_close - danger_line) / danger_line
    
    # 3. Risk Categorization (Clustering):
    if cushion < 0.02:
        status = 'High Risk'      # Critical proximity to the danger zone
    elif cushion < 0.03:
        status = 'Moderate Risk'  # Approaching the threshold; needs monitoring
    else:
        status = 'Low Risk'       # Price is comfortably stabilized
        
    return status, cushion

# Applying the logic across the dataset
data[['Risk_Status', 'Cushion_Pct']] = data.apply(
    lambda row: pd.Series(check_risk(row)), axis=1)

# --- DATA EXPORT ---

# Removing timezone info to ensure compatibility with Excel formatting
data.index = data.index.tz_localize(None)

# Creating a unique filename with a timestamp for audit trailing
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
filename = f"Market_Risk_Report_{TICKER}_{timestamp}.xlsx"

# Exporting the clean dataset for the Excel Dashboard engine
data.to_excel(filename)

print(f"Success! Your analysis report '{filename}' has been created.")
