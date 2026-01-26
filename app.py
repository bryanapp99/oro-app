import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
import feedparser
from streamlit_autorefresh import st_autorefresh

# 1. Configuración Inicial
st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
st_autorefresh(interval=60000, limit=1000, key="gold_update")

# 2. Definir variables de control (ESTO EVITA EL NAMEERROR)
st.sidebar.header("⚙️ Configuración")
intervalo = st.sidebar.selectbox("Temporalidad:", options=["1m", "5m", "15m", "1h", "1d"], index=2)
periodo_map = {"1m": "1d", "5m": "5d", "15m": "7d", "1h": "1mo", "1d": "6mo"}
periodo = periodo_map[intervalo]

# 3. Descarga de Datos
data = yf.download("GC=F", interval=intervalo, period=periodo)

if not data.empty and len(data) > 20:
    df = data.copy()
    if isinstance(df.columns, pd.MultiIndex): 
        df.columns = df.columns.get_level_values(0)

    # Indicadores Técnicos
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    current_price = float(df['Close'].iloc[-1])
    current_rsi = float(df['RSI'].iloc[-1])
    current_ema = float(df['EMA_20'].iloc[-1])

    # Lógica de Señal
    signal = "ESPERAR"
    if current_price > current_ema and current_rsi < 45: signal = "COMPRA"
    elif current_price < current_ema and current_rsi > 55: signal = "VENTA"

    # --- INTERFAZ VISUAL ---
    st.markdown(f"<h1 style='text-align: center; color: #FFD700;'>🥇 XAU/USD TERMINAL</h1>", unsafe_allow_html=True)
    
    # Fila superior: Señal y Simulador
    col_sig, col_calc = st.columns([1, 1])

    with col_sig:
        st.subheader("📢 Señal Actual")
        color = "#28a745" if signal == "COMPRA" else "#dc3545" if signal == "VENTA" else "#6c757d"
        st.markdown(f"""
            <div style='background:{color};padding:20px;border-radius:10px;text-align:center;color:white'>
                <h1>{signal}</h1>
                <p style='font-size:25px;'>${current_price:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)

    with col_calc:
        st.subheader("🧮 Gestión de Riesgo")
        cap = st.number_input("Capital Total ($)", value=1000.0, step=100.0)
        riesgo = st.slider("% de Riesgo", 0.5, 5.0, 1.0)
        dinero = cap * (riesgo/100)
        st.info(f"Riesgo monetario: **${dinero:.2f}**")
        
        if signal != "ESPERAR":
            tp_s = current_price + 5.0 if signal == "COMPRA" else current_price - 5.0
            sl_s = current_price - 3.0 if signal == "COMPRA" else current_price + 3.0
            st.success(f"🎯 TP: {tp_s:.2f} | 🛑 SL: {sl_s:.2f}")

    # --- GRÁFICO DE VELAS ---
    st.write("---")
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], 
        low=df['Low'], close=df['Close'], name="Precio"
    )])
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], line=dict(color='yellow', width=1.5), name='Trend'))
    fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

    # --- NOTICIAS ---
    with st.expander("📰 Ver últimas noticias del mercado"):
        feed = feedparser.parse("https://www.investing.com/rss/news_1.rss")
        for entry in feed.entries[:5]:
            st.markdown(f"• [{entry.title}]({entry.link})")
else:
    st.warning("Cargando datos del mercado de Oro... Si el error persiste, verifica que el mercado esté abierto.")
