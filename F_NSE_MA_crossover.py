
import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(
    page_title="MA Crossover Scanner",
    layout="wide"
)

# ============================================================
# SETTINGS
# ============================================================

# sp500 = pd.read_csv("D:/Py/ind_nifty500list_1_1.csv")
# sym_list = sorted(sp500["Symbol"].dropna().unique())[:10]

master = pd.read_csv("ind_nifty500list_1.csv")

master["Symbol"] = (
    master["Symbol"]
    .astype(str)
    .str.strip()
)

 

# ============================================================
# YAHOO TICKERS
# ============================================================

sym_list = (
    master["Symbol"] + ".NS"
).tolist()


# ============================================================
# PROCESS SYMBOL
# ============================================================

def process_symbol(ticker):

    data = yf.download(
        ticker,
        period="1y",
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    if data.empty:
        return None

    # Handle yfinance MultiIndex columns
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data[["Close"]].dropna().copy()

    data["MA20"] = data["Close"].rolling(20).mean()
    data["MA50"] = data["Close"].rolling(50).mean()

    # Bullish crossover
    data["CrossOver"] = (
        (data["MA20"] > data["MA50"]) &
        (data["MA20"].shift(1) <= data["MA50"].shift(1))
    )

    # Bearish crossover
    data["CrossUnder"] = (
        (data["MA20"] < data["MA50"]) &
        (data["MA20"].shift(1) >= data["MA50"].shift(1))
    )

    events = data[data["CrossOver"] | data["CrossUnder"]]

    if events.empty:
        return None

    # Latest crossover
    last_date = events.index[-1]
    last_event = events.iloc[-1]

    crossover_price = float(last_event["Close"])
    latest_price = float(data["Close"].iloc[-1])

    # Percentage change since crossover
    change_pct = (
        (latest_price / crossover_price) - 1
    ) * 100

    latest_date = data.index[-1]

    days_since_crossover = len(
    data.loc[(data.index > last_date) & (data.index <= latest_date)]
    )

    return {
        "Symbol": ticker,
        "Last Crossover Date": last_date.strftime("%Y-%m-%d"),
        "Signal": (
            "Bullish" if last_event["CrossOver"]
            else "Bearish"
        ),
        "Crossover Price": round(crossover_price, 2),
        "Latest Price": round(latest_price, 2),
        "Change Since Crossover %": round(change_pct, 2),
        "Last Crossover Date": last_date.strftime("%Y-%m-%d"),
        "Days Since Crossover": days_since_crossover,
        "Signal": (
        "Bullish" if last_event["CrossOver"]
        else "Bearish"
        ),
    }


# ============================================================
# STREAMLIT DASHBOARD
# ============================================================

st.title("📊 MA20 / MA50 Crossover Scanner")

if st.button("Run Scanner"):

    results = []
    progress = st.progress(0)

    for i, ticker in enumerate(sym_list):

        try:
            result = process_symbol(ticker)

            if result is not None:
                results.append(result)

        except Exception as e:
            st.warning(f"Error processing {ticker}: {e}")

        progress.progress((i + 1) / len(sym_list))

    progress.empty()

    df = pd.DataFrame(results)

    if not df.empty:

        df = df.sort_values(
            "Last Crossover Date",
            ascending=False
        ).reset_index(drop=True)

        st.subheader("Latest Crossover Results")

        # Create TradingView hyperlinks
        
        df["Chart"] = (
            "https://www.tradingview.com/chart/?symbol=NSE:"
            + df["Symbol"].astype(str).str.replace(r"\.NS$", "", regex=True)
        )
    
        df["Yahoo Finance"] = (
            "https://finance.yahoo.com/quote/"
            + df["Symbol"].astype(str)            
        )
    
        df["News"] = (
            "https://www.google.com/search?q="
            + df["Symbol"].astype(str).str.replace(r"\.NS$", "", regex=True)
            + "+stock+news"
        )
    
        st.dataframe(
            df,
            column_config={
                "Chart": st.column_config.LinkColumn(
                    "TradingView",
                    display_text="Open Chart"
                ),
                "Yahoo Finance": st.column_config.LinkColumn(
                    "Yahoo Finance",
                    display_text="Open Quote"
                ),
                "News": st.column_config.LinkColumn(
                    "Latest News",
                    display_text="View News"
                )
            },
            hide_index=True,
            width='content'
        )       

        st.download_button(
            "⬇️ Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="latest_ma_crossover.csv",
            mime="text/csv"
        )

    else:
        st.info("No crossover signals found.")

     