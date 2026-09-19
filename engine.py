import yfinance as yf
import pandas as pd
import numpy as np

def calculate_technical_indicators(df):
    """
    Пресметува RSI (14), Bollinger Bands (20, 2) и ATR (14).
    """
    # 1. RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # 2. Bollinger Bands (20, 2)
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['STD_20'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['SMA_20'] + (2 * df['STD_20'])
    df['BB_Lower'] = df['SMA_20'] - (2 * df['STD_20'])

    # 3. ATR (Average True Range - 14)
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()

    return df

def get_financial_data(symbols):
    """
    Презема историски цени и аналитички податоци за листата на тикери.
    """
    formatted_symbols = []
    symbol_map = {}

    for sym in symbols:
        yf_sym = sym
        if "LON:" in sym:
            yf_sym = sym.replace("LON:", "") + ".L"
        elif ":" in sym:
            yf_sym = sym.split(":")[1]
        
        formatted_symbols.append(yf_sym)
        symbol_map[yf_sym] = sym

    # Batch download за историски цени
    raw_data = yf.download(formatted_symbols, period="6mo", group_by='ticker', progress=False)

    results = []

    for yf_sym in formatted_symbols:
        original_sym = symbol_map[yf_sym]
        
        if len(formatted_symbols) == 1:
            df = raw_data.copy()
        else:
            if yf_sym not in raw_data or raw_data[yf_sym].dropna().empty:
                continue
            df = raw_data[yf_sym].dropna().copy()

        if df.empty:
            continue

        # Пресметка на технички индикатори
        df = calculate_technical_indicators(df)

        last_row = df.iloc[-1]
        current_price = float(last_row['Close'])

        # Прилагодување за LSE (пенси во фунти)
        if yf_sym.endswith(".L") and "VUAA" not in yf_sym:
            if current_price > 500:
                current_price = current_price / 100.0

        current_rsi = float(last_row['RSI'])
        bb_lower = float(last_row['BB_Lower'])
        bb_upper = float(last_row['BB_Upper'])
        atr = float(last_row['ATR'])

        # Динамички Dip и TP Нивоа
        mod_dip = round(bb_lower, 2)
        strong_dip = round(bb_lower - (0.5 * atr), 2)
        mod_tp = round(bb_upper, 2)
        strong_tp = round(bb_upper + (0.5 * atr), 2)

        # Логика за Аларм за Цена (Price Signal)
        price_status = "NEUTRAL"
        if current_price <= strong_dip:
            price_status = "STRONG DIP ALERT"
        elif current_price <= mod_dip:
            price_status = "MOD DIP ALERT"
        elif current_price >= strong_tp:
            price_status = "STRONG TP ALERT"
        elif current_price >= mod_tp:
            price_status = "MOD TP ALERT"

        # Логика за Аларм за RSI (RSI Signal)
        rsi_status = "NORMAL"
        if current_rsi <= 30:
            rsi_status = "OVERSOLD (BUY)"
        elif current_rsi >= 70:
            rsi_status = "OVERBOUGHT (SELL)"

        # Извлекување аналитички таргети
        analyst_rec = "N/A"
        target_high = None
        target_low = None
        target_mean = None
        
        try:
            ticker_info = yf.Ticker(yf_sym).info
            rec_val = ticker_info.get("recommendationKey")
            if rec_val:
                analyst_rec = rec_val.replace("_", " ").upper()
            
            if ticker_info.get("targetHighPrice") is not None:
                target_high = round(float(ticker_info.get("targetHighPrice")), 2)
            if ticker_info.get("targetLowPrice") is not None:
                target_low = round(float(ticker_info.get("targetLowPrice")), 2)
            if ticker_info.get("targetMeanPrice") is not None:
                target_mean = round(float(ticker_info.get("targetMeanPrice")), 2)
        except Exception:
            pass

        # Price Signal е веднаш по Price (3-та колона)
        results.append({
            "Ticker": original_sym,
            "Price": round(current_price, 2),
            "Price Signal": price_status,
            "Mod Dip": mod_dip,
            "Strong Dip": strong_dip,
            "Mod TP": mod_tp,
            "Strong TP": strong_tp,
            "RSI (14)": round(current_rsi, 2),
            "RSI Signal": rsi_status,
            "Analyst Rec": analyst_rec,
            "Target High": target_high,
            "Target Low": target_low,
            "Target Mean": target_mean
        })

    return pd.DataFrame(results)