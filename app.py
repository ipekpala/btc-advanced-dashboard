import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------
# CONFIG
# ---------------------------------
st.set_page_config(
    page_title="BTC Advanced Dashboard",
    page_icon="₿",
    layout="wide",
)


GITHUB_URL = "https://github.com/ipekpala"
LINKEDIN_URL = "www.linkedin.com/in/ipek-pala-17a7052a2"

# ---------------------------------
# CUSTOM UI
# ---------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(59,130,246,0.18), transparent 28%),
        radial-gradient(circle at top right, rgba(16,185,129,0.10), transparent 25%),
        linear-gradient(135deg, #0f172a 0%, #020617 55%, #000000 100%);
    color: #f8fafc;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1250px;
}

h1, h2, h3, h4, h5, h6, p, label, div, span {
    color: #f8fafc !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617 0%, #0f172a 100%);
    border-right: 1px solid rgba(255,255,255,0.08);
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div {
    color: #e2e8f0 !important;
}

[data-testid="metric-container"] {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.09);
    backdrop-filter: blur(10px);
    border-radius: 18px;
    padding: 18px 18px 14px 18px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.20);
}

div[data-testid="stMarkdownContainer"] p {
    font-size: 15px;
}

.stButton > button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: white !important;
    border: none;
    border-radius: 12px;
    padding: 0.55rem 1rem;
    font-weight: 600;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white !important;
}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="slider"] {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 12px !important;
}

[data-testid="stDataFrame"] {
    background: rgba(255,255,255,0.04);
    border-radius: 16px;
    padding: 8px;
    border: 1px solid rgba(255,255,255,0.06);
}

[data-testid="stExpander"] {
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    background: rgba(255,255,255,0.03);
}

hr {
    border-color: rgba(255,255,255,0.08);
}

.footer-wrap {
    margin-top: 40px;
    padding: 22px 0 12px 0;
    text-align: center;
    border-top: 1px solid rgba(255,255,255,0.08);
}

.footer-main {
    font-size: 14px;
    color: rgba(255,255,255,0.72) !important;
}

.footer-links {
    margin-top: 8px;
    font-size: 13px;
}

.footer-links a {
    color: #93c5fd !important;
    text-decoration: none;
    margin: 0 10px;
}

.footer-links a:hover {
    text-decoration: underline;
}

::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-thumb {
    background: #3b82f6;
    border-radius: 10px;
}
::-webkit-scrollbar-track {
    background: rgba(255,255,255,0.04);
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------
# HELPERS
# ---------------------------------
def format_currency(value: float) -> str:
    return f"${value:,.2f}"

def format_large_number(value: float) -> str:
    if value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.2f}K"
    return f"${value:,.2f}"

def safe_request(url: str, params: dict | None = None):
    try:
        response = requests.get(url, params=params, timeout=20)
        if response.status_code == 429:
            raise RuntimeError("API rate limit reached. Biraz bekleyip tekrar dene.")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out. İnternet bağlantını kontrol edip tekrar dene.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Connection error. API'ye bağlanılamadı.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"HTTP error: {e}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request failed: {e}")

# ---------------------------------
# DATA
# ---------------------------------
@st.cache_data(ttl=180)
def get_btc_market_data(days: int) -> pd.DataFrame:
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily",
    }
    data = safe_request(url, params)

    prices = data.get("prices", [])
    volumes = data.get("total_volumes", [])

    if not prices:
        raise RuntimeError("BTC historical data could not be loaded.")

    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")

    volume_values = [v[1] for v in volumes[:len(df)]]
    if len(volume_values) < len(df):
        volume_values += [None] * (len(df) - len(volume_values))

    df["volume"] = volume_values
    df["open"] = df["price"].shift(1)
    df["close"] = df["price"]
    df["high"] = df[["open", "close"]].max(axis=1)
    df["low"] = df[["open", "close"]].min(axis=1)

    df = df.dropna().copy()
    df["daily_return_pct"] = df["close"].pct_change() * 100
    df["ma7"] = df["close"].rolling(7).mean()
    df["ma30"] = df["close"].rolling(30).mean()
    df["volatility_7d"] = df["daily_return_pct"].rolling(7).std()

    return df

@st.cache_data(ttl=90)
def get_btc_live_data():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_market_cap": "true",
        "include_24hr_vol": "true",
    }
    data = safe_request(url, params)

    if "bitcoin" not in data:
        raise RuntimeError("BTC live data could not be loaded.")

    return data["bitcoin"]

@st.cache_data(ttl=300)
def get_fear_and_greed():
    url = "https://api.alternative.me/fng/"
    data = safe_request(url)
    items = data.get("data", [])
    if not items:
        raise RuntimeError("Fear & Greed data could not be loaded.")
    latest = items[0]
    return {
        "value": int(latest["value"]),
        "classification": latest["value_classification"],
    }

# ---------------------------------
# LOGIC
# ---------------------------------
def get_risk_level(pnl_pct: float, change_24h: float, volatility: float) -> str:
    if pnl_pct < -15 or change_24h < -5 or volatility > 6:
        return "HIGH"
    if pnl_pct < -5 or change_24h < -2 or volatility > 3:
        return "MEDIUM"
    return "LOW"

def build_insight(current_price: float, change_24h: float, pnl_pct: float, target_price: float, risk_level: str) -> str:
    messages = []

    if change_24h > 3:
        messages.append("Short-term momentum looks strong.")
    elif change_24h < -3:
        messages.append("Short-term weakness is visible.")
    else:
        messages.append("Price action is relatively balanced.")

    if pnl_pct > 10:
        messages.append("Your position is in strong profit.")
    elif pnl_pct < -10:
        messages.append("Your position is under pressure.")
    else:
        messages.append("Your position is near a neutral zone.")

    distance_pct = ((target_price - current_price) / current_price) * 100
    if distance_pct >= 0:
        messages.append(f"Your target is {distance_pct:.2f}% above the current price.")
    else:
        messages.append(f"Your target is {abs(distance_pct):.2f}% below the current price.")

    messages.append(f"Overall risk level: {risk_level}.")
    return " ".join(messages)

def build_sentiment_box(value: int, classification: str):
    st.subheader("Market Sentiment")
    label = f"{classification} ({value})"

    if value < 25:
        st.error(label)
    elif value < 50:
        st.warning(label)
    elif value < 75:
        st.success(label)
    else:
        st.success(label)

def create_candlestick_chart(df: pd.DataFrame, target_price: float, scenario_price: float):
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="BTC",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["ma7"],
            mode="lines",
            name="MA7",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["ma30"],
            mode="lines",
            name="MA30",
        )
    )

    fig.add_hline(
        y=target_price,
        line_width=1,
        line_dash="dash",
        annotation_text="Target",
        annotation_position="top left",
    )

    fig.add_hline(
        y=scenario_price,
        line_width=1,
        line_dash="dot",
        annotation_text="Scenario",
        annotation_position="bottom left",
    )

    fig.update_layout(
        title="BTC Candlestick Chart",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        hovermode="x unified",
        height=580,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_rangeslider_visible=False,
    )

    return fig

def create_profit_heatmap(buy_price: float, btc_amount: float):
    multipliers = [0.70, 0.80, 0.90, 1.00, 1.10, 1.20, 1.30]
    scenario_prices = [buy_price * m for m in multipliers]
    labels = [f"{int((m-1)*100):+d}%" for m in multipliers]
    pnl_values = [(price - buy_price) * btc_amount for price in scenario_prices]

    heatmap_df = pd.DataFrame([pnl_values], columns=labels, index=["P/L"])
    text_values = [[format_currency(v) for v in pnl_values]]

    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_df.values,
            x=heatmap_df.columns,
            y=heatmap_df.index,
            text=text_values,
            texttemplate="%{text}",
            textfont={"size": 14},
            colorscale="RdYlGn",
            zmid=0,
            hovertemplate="Scenario: %{x}<br>P/L: %{text}<extra></extra>",
        )
    )

    fig.update_layout(
        title="Profit Heatmap by Price Scenario",
        xaxis_title="Price Change vs Buy Price",
        yaxis_title="",
        height=250,
        margin=dict(l=10, r=10, t=50, b=10),
    )

    return fig

# ---------------------------------
# SIDEBAR
# ---------------------------------
st.sidebar.title("Control Panel")

days = st.sidebar.selectbox("Time Range", [7, 30, 90, 180, 365], index=1)
buy_price = st.sidebar.number_input("Buy Price (USD)", min_value=0.0, value=85000.0, step=100.0)
btc_amount = st.sidebar.number_input("BTC Amount", min_value=0.0, value=0.25, step=0.01)
target_price = st.sidebar.number_input("Target Price (USD)", min_value=0.0, value=100000.0, step=100.0)
scenario_price = st.sidebar.number_input("Scenario Price (USD)", min_value=0.0, value=90000.0, step=100.0)

simulated_price = st.sidebar.slider(
    "Simulated BTC Price",
    min_value=20000,
    max_value=200000,
    value=90000,
    step=500
)

refresh_data = st.sidebar.button("Refresh Data")
if refresh_data:
    st.cache_data.clear()

# ---------------------------------
# MAIN UI
# ---------------------------------
st.title("₿ BTC Advanced Dashboard")
st.caption("Professional Bitcoin analysis dashboard with simulator, sentiment tracking, and heatmap")

try:
    df = get_btc_market_data(days)
    live = get_btc_live_data()
    fng = get_fear_and_greed()

    current_price = float(live["usd"])
    change_24h = float(live.get("usd_24h_change", 0.0))
    market_cap = float(live.get("usd_market_cap", 0.0))
    volume_24h = float(live.get("usd_24h_vol", 0.0))

    position_value = btc_amount * current_price
    cost_basis = btc_amount * buy_price
    pnl = position_value - cost_basis
    pnl_pct = ((current_price - buy_price) / buy_price * 100) if buy_price > 0 else 0.0

    simulated_value = btc_amount * simulated_price
    simulated_pnl = simulated_value - cost_basis
    simulated_pnl_pct = ((simulated_price - buy_price) / buy_price * 100) if buy_price > 0 else 0.0

    scenario_value = btc_amount * scenario_price
    scenario_pnl = scenario_value - cost_basis

    break_even_price = buy_price
    break_even_diff_pct = ((break_even_price - current_price) / current_price * 100) if current_price > 0 else 0.0

    period_high = float(df["close"].max())
    period_low = float(df["close"].min())
    avg_price = float(df["close"].mean())

    latest_volatility = df["volatility_7d"].dropna()
    volatility = float(latest_volatility.iloc[-1]) if not latest_volatility.empty else 0.0

    risk = get_risk_level(pnl_pct, change_24h, volatility)
    simulated_risk = get_risk_level(simulated_pnl_pct, change_24h, volatility)
    target_distance_pct = ((target_price - current_price) / current_price * 100) if current_price > 0 else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("BTC Price", format_currency(current_price), f"{change_24h:.2f}%")
    m2.metric("Portfolio Value", format_currency(position_value))
    m3.metric("P/L", format_currency(pnl), f"{pnl_pct:.2f}%")
    m4.metric("24h Volume", format_large_number(volume_24h))

    st.subheader("Price Simulator")
    s1, s2, s3 = st.columns(3)
    s1.metric("Simulated Price", format_currency(simulated_price))
    s2.metric("Simulated Value", format_currency(simulated_value))
    s3.metric("Simulated P/L", format_currency(simulated_pnl), f"{simulated_pnl_pct:.2f}%")

    st.plotly_chart(
        create_candlestick_chart(df, target_price, scenario_price),
        use_container_width=True
    )

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Period High", format_currency(period_high))
    a2.metric("Period Low", format_currency(period_low))
    a3.metric("7D Volatility", f"{volatility:.2f}%")
    a4.metric("Target Distance", f"{target_distance_pct:.2f}%")

    b1, b2 = st.columns(2)
    b1.metric("Break-even Price", format_currency(break_even_price))
    b2.metric("Break-even Distance", f"{break_even_diff_pct:.2f}%")

    st.plotly_chart(
        create_profit_heatmap(buy_price, btc_amount),
        use_container_width=True
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Position Summary")
        st.write(f"**Cost Basis:** {format_currency(cost_basis)}")
        st.write(f"**Average Price:** {format_currency(avg_price)}")
        st.write(f"**Market Cap:** {format_large_number(market_cap)}")
        st.write(f"**Risk Level:** {risk}")
        st.write(f"**Selected Range:** {days} days")

    with right:
        build_sentiment_box(fng["value"], fng["classification"])
        st.write(f"**Scenario Value:** {format_currency(scenario_value)}")
        st.write(f"**Scenario P/L:** {format_currency(scenario_pnl)}")
        st.write(f"**Target Price:** {format_currency(target_price)}")
        st.write(f"**Simulated Risk:** {simulated_risk}")

    st.subheader("Current Position Insight")
    current_insight = build_insight(current_price, change_24h, pnl_pct, target_price, risk)

    if risk == "HIGH":
        st.error(current_insight)
    elif risk == "MEDIUM":
        st.warning(current_insight)
    else:
        st.success(current_insight)

    st.subheader("Simulation Insight")
    simulation_insight = build_insight(simulated_price, change_24h, simulated_pnl_pct, target_price, simulated_risk)

    if simulated_risk == "HIGH":
        st.error(simulation_insight)
    elif simulated_risk == "MEDIUM":
        st.warning(simulation_insight)
    else:
        st.success(simulation_insight)

    with st.expander("Recent Market Data"):
        display_df = df.tail(10).copy()
        display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
        st.dataframe(
            display_df[["date", "open", "high", "low", "close", "volume", "daily_return_pct", "ma7", "ma30"]],
            use_container_width=True,
        )

except Exception as e:
    st.error(str(e))

# ---------------------------------
# FOOTER
# ---------------------------------
st.markdown(
    f"""
    <div class="footer-wrap">
        <div class="footer-main">
            Built by <b>İpek Pala</b> • BTC Advanced Dashboard
        </div>
        <div class="footer-links">
            <a href="{GITHUB_URL}" target="_blank">GitHub</a>
            <a href="{LINKEDIN_URL}" target="_blank">LinkedIn</a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
