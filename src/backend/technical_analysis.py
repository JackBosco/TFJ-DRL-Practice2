# Refactored functions for retrieving statistics for technical analysis outside of notebook 
# for easier reusibility + readibility
# @Author Jack Bosco

from collections import defaultdict
import numpy as np
import yfinance as yf
import talib as ta
import statsmodels.tsa.stattools as ts

#read daily stock data series from yahoo finance
def get_data(name, start="2017-01-01", end="2020-01-01"):
    # Use yfinance to download historical stock data
    ticker = yf.Ticker(name)
    data = ticker.history(start=start, end=end)
    # Drop columns not needed for analysis such as 'Dividends' and 'Stock Splits'
    return data.drop(['Dividends', 'Stock Splits'], axis=1, errors='ignore')

# Function to calculate technical analysis indicators and add them to the dataset
# The set of indicators here are expandable
def calc_tech_ind(data):
    # Calculate Bollinger Bands and add to the dataset
    data['upbd'], data['midbd'], data['lowbd'] = ta.BBANDS(data["Close"])
    # Calculate Double Exponential Moving Average and add to dataset
    data['dema'] = ta.DEMA(data["Close"], timeperiod=30)
    # Calculate Triple Exponential Moving Average and add to dataset
    data['tema'] = ta.TEMA(data["Close"], timeperiod=30)
    # Calculate Exponential Moving Average and add to dataset
    data['ema'] = ta.EMA(data["Close"], timeperiod=30)
    # Calculate Weighted Moving Average and add to dataset
    data['wma'] = ta.WMA(data["Close"], timeperiod=30)
    # Calculate Simple Moving Average and add to dataset
    data['sma'] = ta.SMA(data["Close"], timeperiod=30)
    # Calculate Parabolic SAR Extended and add to dataset
    data['sarext'] = ta.SAREXT(data["High"], data["Low"])
    
    # Momentum indicators
    # Calculate Average Directional Movement Index Rating and add to dataset
    data['adxr'] = ta.ADXR(data["High"], data["Low"], data["Close"], timeperiod=14)
    # Calculate Absolute Price Oscillator and add to dataset
    data['apo'] = ta.APO(data["Close"], fastperiod=12, slowperiod=26, matype=0)
    # Calculate Aroon Oscillator Down and Up and add to dataset
    data['aroondown'], data['aroonup'] = ta.AROON(data["High"], data["Low"], timeperiod=14)
    # Calculate Commodity Channel Index and add to dataset
    data['cci'] = ta.CCI(data["High"], data["Low"], data["Close"], timeperiod=14)
    # Calculate Chande Momentum Oscillator and add to dataset
    data['cmo'] = ta.CMO(data["Close"], timeperiod=14)
    # Calculate Moving Average Convergence/Divergence and add to dataset
    data['macd'], data['macdsignal'], data['macdhist'] = ta.MACD(data["Close"], fastperiod=12, slowperiod=26, signalperiod=9)
    # Calculate Money Flow Index and add to dataset
    data['MFI'] = ta.MFI(data["High"], data["Low"], data["Close"], data['Volume'], timeperiod=14)
    # Calculate Momentum Indicator and add to dataset
    data['mom'] = ta.MOM(data["Close"], timeperiod=10)
    # Calculate Plus Directional Indicator and add to dataset
    data['plus_di'] = ta.PLUS_DI(data["High"], data["Low"], data["Close"], timeperiod=14)
    # Calculate Percentage Price Oscillator and add to dataset
    data['ppo'] = ta.PPO(data["Close"], fastperiod=12, slowperiod=26, matype=0)
    # Calculate Rate of Change and add to dataset
    data['roc'] = ta.ROC(data["Close"], timeperiod=10)
    # Calculate Rate of Change Percentage and add to dataset
    data['rocp'] = ta.ROCP(data["Close"], timeperiod=10)
    # Calculate Relative Strength Index and add to dataset
    data['rsi'] = ta.RSI(data["Close"], timeperiod=14)
    # Calculate Stochastic Oscillator Slow (%K and %D) and add to dataset
    data['slowk'], data['slowd'] = ta.STOCH(data["High"], data["Low"], data["Close"])
    # Calculate Stochastic Fast (%K and %D) and add to dataset
    data['fastk'], data['fastd'] = ta.STOCHF(data["High"], data["Low"], data["Close"])
    # Calculate Triple Exponential Average Oscillator and add to dataset
    data['trix'] = ta.TRIX(data["Close"], timeperiod=30)
    # Calculate Ultimate Oscillator and add to dataset
    data['ultosc'] = ta.ULTOSC(data["High"], data["Low"], data["Close"], timeperiod1=7, timeperiod2=14, timeperiod3=28)
    # Calculate Williams %R and add to dataset
    data['willr'] = ta.WILLR(data["High"], data["Low"], data["Close"], timeperiod=14)
    
    # Volume indicators
    # Calculate Accumulation/Distribution Line and add to dataset
    data['ad'] = ta.AD(data["High"], data["Low"], data["Close"], data['Volume'])
    # Calculate On-Balance Volume and add to dataset
    data['obv'] = ta.OBV(data["Close"], data['Volume'])
    
    # Volatility indicators
    # Calculate Average True Range and add to dataset
    data['atr'] = ta.ATR(data["High"], data["Low"], data["Close"], timeperiod=14)
    # Calculate Normalized Average True Range and add to dataset
    data['natr'] = ta.NATR(data["High"], data["Low"], data["Close"], timeperiod=14)
    
    # Cycle indicators
    # Calculate Hilbert Transform Dominant Cycle Period and add to dataset
    data['HT_DCPERIOD'] = ta.HT_DCPERIOD(data["Close"])
    # Calculate Hilbert Transform Dominant Cycle Phase and add to dataset
    data['HT_DCPHASE'] = ta.HT_DCPHASE(data["Close"])
    # Calculate Hilbert Transform Phasor Components and add to dataset
    data['inphase'], data['quadrature'] = ta.HT_PHASOR(data["Close"])
    
    return data

# Function to get a combined dataset of multiple stocks with technical indicators calculated
def get_data_set(name_list: list[str], start="2017-01-01", end="2020-01-01", verbose: bool = False, coint_threshold: float|None = 0.1) -> np.array:
    """Function to get a combined dataset of multiple stocks with technical indicators calculated

    Args:
        name_list (list[str]): List of ticker names as strings, must be all caps
        start (str, optional): The start date for the time horizon. Must be formatted "YYYY-MM-DD". Defaults to "2017-01-01".
        end (str, optional): The end date for the time horizon. Must be formatted "YYYY-MM-DD". Defaults to "2020-01-01".
        verbose (bool, optional): Whether to print information about the size of the dataset. Defaults to False.
        coint_threshold (float|None, optional): Maxumum p-value threshold for determining cointigration between two stocks using MacKinnon's approximate, asymptotic p-value based on MacKinnon (1994). If None, do not calculate cointigration. Defaults to 0.1.  
        

    Returns:
        numpy.array: An array of dimensions N x D x F where 
            N = the number of ticker names
            D = the number of days in the given time horizon
            F = the number of technical indicators / features defined in calc_tech_ind 
    """
    data_list = []
    # Loop through each stock in the name_list and calculate technical indicators
    for name in name_list:
        data_list.append(calc_tech_ind(get_data(name, start, end)).iloc[90:].fillna(0).values)
    
    # Get the number of features from the original dataset
    feature_count = data_list[0].shape[1]
    output_coints = defaultdict(list)
    # Calculate cointegration between stocks
    for i in range(len(data_list)):
        high_correlation_list = []
        for j in range(len(data_list)):
            if i != j and coint_threshold:
                coint = ts.coint(data_list[i][:, 3], data_list[j][:, 3])[1] 
                if coint <= coint_threshold:
                    high_correlation_list.append(j)
                    output_coints[i].append(j)
                    
        # Append features of highly cointegrated stocks to the dataset
        avg_features = np.zeros((data_list[i].shape[0], data_list[i].shape[1] - 4))
        for k in high_correlation_list:
            feature = data_list[k][:, 4:feature_count]
            # standardize using standard vector
            avg_features += (feature - feature.mean(axis=0, keepdims=True)) / (feature.std(axis=0, keepdims=True))
        if avg_features.sum() != 0:
            avg_features = avg_features / len(high_correlation_list)
        # Concatenate average features to the main dataset
        data_list[i] = np.concatenate([data_list[i], avg_features], axis=1)
    
    if verbose:
        print(f"Retrieved Technical Indicators. Output size {len(data_list)} stocks x {data_list[0].shape[0]} days x {data_list[0].shape[1]} indicators")
        print("Highly cointigrated stocks:")
        for key_idx in output_coints.keys():
            print(f"\t{name_list[key_idx]:4s}", end=': [')
            vals = ""
            for val_idx in output_coints[key_idx]:
                vals += f"{name_list[val_idx]:4s}, "
            print(vals[:-3] + "]")
    
    return np.array(data_list)