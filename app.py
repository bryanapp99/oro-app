import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
import feedparser
from streamlit_autorefresh import st_autorefresh # <-- Nueva librería

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")

# CONFIGURACIÓN DE AUTO-REFRESCO: 60000 milisegundos = 1 minuto
st_autorefresh(interval=60000, limit=1000, key="gold_update")

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Configuración")
intervalo = st.sidebar.selectbox(
    "Selecciona Temporalidad:",
    options=["1m", "5m", "15m", "1h", "1d"],
    index=2
)

# Mapeo de periodos
periodo_map = {"1m": "1d", "5m": "5d", "15m": "7d", "1h": "1mo", "1d": "6mo"}
periodo = periodo_map[intervalo]

st.markdown(f"<h1 style='text-align: center; color: #FFD700;'>🥇 XAU/USD LIVE ({intervalo})</h1>", unsafe_allow_html=True)
st.caption(f"🔄 La app se actualiza automáticamente cada 60 segundos.")

# 1. Función de Noticias
def get_news():
    try:
        feed = feedparser.parse("https://www.investing.com/rss/news_1.rss")
        return [{"title": entry.title, "link": entry.link} for entry in feed.entries[:5]]
    except:
        return []

# 2. Obtener Datos
data = yf.download("GC=F", interval=intervalo, period=periodo)

if not data.empty and len(data) > 20:
    df = data.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 3. Indicadores
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    current_price = float(df['Close'].iloc[-1])
    current_rsi = float(df['RSI'].iloc[-1])
    current_ema = float(df['EMA_20'].iloc[-1])

    # --- SECCIÓN SUPERIOR ---
    col_sig, col_news = st.columns([1, 1.5])

    with col_sig:
        st.subheader(f"📢 Señal {intervalo}")
        if current_price > current_ema and current_rsi < 40:
            st.success("🚀 COMPRA (BUY)")
        elif current_price < current_ema and current_rsi > 60:
            st.error("🔥 VENTA (SELL)")
        else:
            st.warning("⚖️ ESPERAR")
        st.metric("Precio Actual", f"${current_price:,.2f}", delta=f"{current_price - df['Open'].iloc[-1]:.2f}")

    with col_news:
        st.subheader("📰 Noticias Recientes")
        for item in get_news():
            st.markdown(f"• [{item['title']}]({item['link']})")

    # --- SECCIÓN GRÁFICO ---
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Velas"
    )])
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], line=dict(color='yellow', width=1.5), name='EMA 20'))
    fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Esperando datos del mercado... (El mercado abre domingos 6PM EST)")
