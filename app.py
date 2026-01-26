import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
import feedparser
from streamlit_autorefresh import st_autorefresh

# 1. CONFIGURACIÓN Y MEMORIA
st.set_page_config(page_title="Gold Master Pro", layout="wide")
if 'historial' not in st.session_state:
    st.session_state.historial = []

# Auto-refresco cada 1 minuto
st_autorefresh(interval=60000, limit=1000, key="gold_ultra_update")

# 2. BARRA LATERAL (AJUSTES)
st.sidebar.header("⚙️ Parámetros")
intervalo = st.sidebar.selectbox("Temporalidad:", options=["1m", "5m", "15m", "1h", "1d"], index=2)
periodo_map = {"1m": "1d", "5m": "5d", "15m": "7d", "1h": "1mo", "1d": "6mo"}
periodo = periodo_map[intervalo]

# 3. FUNCIÓN DE SONIDO
def play_alert():
    audio_html = """<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg"></audio>"""
    st.components.v1.html(audio_html, height=0)

# 4. OBTENCIÓN Y CÁLCULO (Lógica TradingView + App)
data = yf.download("GC=F", interval=intervalo, period=periodo)

if not data.empty and len(data) > 50:
    df = data.copy()
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # Indicadores del Script TradingView
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    df['EMA_50'] = ta.ema(df['Close'], length=50)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    # Detección de Velas Envolventes (Price Action)
    df['Bullish_Eng'] = (df['Close'] > df['Open']) & (df['Close'].shift(1) < df['Open'].shift(1)) & \
                        (df['Close'] > df['Open'].shift(1)) & (df['Open'] < df['Close'].shift(1))
    
    df['Bearish_Eng'] = (df['Close'] < df['Open']) & (df['Close'].shift(1) > df['Open'].shift(1)) & \
                        (df['Close'] < df['Open'].shift(1)) & (df['Open'] > df['Close'].shift(1))

    # Niveles Fibo simplificados (del Pivot High/Low)
    high_f = df['High'].tail(20).max()
    low_f = df['Low'].tail(20).min()
    fib618 = high_f - (high_f - low_f) * 0.618
    fib382 = high_f - (high_f - low_f) * 0.382

    # Valores Actuales
    cp = float(df['Close'].iloc[-1])
    ema20 = float(df['EMA_20'].iloc[-1])
    ema50 = float(df['EMA_50'].iloc[-1])
    rsi = float(df['RSI'].iloc[-1])
    is_bull = df['Bullish_Eng'].iloc[-1]
    is_bear = df['Bearish_Eng'].iloc[-1]

    # 5. LÓGICA DE SEÑAL MAESTRA
    signal = "ESPERAR"
    # Compra: Tendencia alcista + Vela Envolvente + RSI sano
    if ema20 > ema50 and is_bull and rsi < 65:
        signal = "COMPRA"
    # Venta: Tendencia bajista + Vela Envolvente + RSI sano
    elif ema20 < ema50 and is_bear and rsi > 35:
        signal = "VENTA"

    if signal != "ESPERAR":
        if not st.session_state.historial or st.session_state.historial[-1]['time'] != df.index[-1]:
            st.session_state.historial.append({"time": df.index[-1], "price": cp, "type": signal})
            play_alert()

    # --- INTERFAZ VISUAL ---
    st.markdown(f"<h1 style='text-align: center; color: #FFD700;'>🥇 GOLD MASTER TERMINAL</h1>", unsafe_allow_html=True)
    
    col_sig, col_calc = st.columns([1, 1])
    with col_sig:
        st.subheader("📢 Señal (Fusión TV + App)")
        color = "#28a745" if signal == "COMPRA" else "#dc3545" if signal == "VENTA" else "#6c757d"
        st.markdown(f"<div style='background:{color};padding:20px;border-radius:10px;text-align:center;color:white'><h1>{signal}</h1><p style='font-size:22px;'>Precio: ${cp:,.2f}</p></div>", unsafe_allow_html=True)

    with col_calc:
        st.subheader("🧮 Gestión de Riesgo")
        cap = st.number_input("Capital Cuenta ($)", value=1000.0)
        riesgo = st.slider("% Riesgo", 0.5, 5.0, 1.0)
        st.info(f"Dinero en riesgo: **${(cap * (riesgo/100)):.2f}**")
        if signal != "ESPERAR":
            st.success(f"🎯 TP Sugerido: {cp + 5:.2f} | 🛑 SL Sugerido: {cp - 3:.2f}" if signal == "COMPRA" else f"🎯 TP: {cp - 5:.2f} | 🛑 SL: {cp + 3:.2f}")

    # --- GRÁFICO ---
    st.write("---")
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Velas")])
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], line=dict(color='orange', width=1.5), name='EMA 20 (Rápida)'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='blue', width=1.5), name='EMA 50 (Lenta)'))
    
    # Marcar Señales Históricas con flechas
    for s in st.session_state.historial:
        fig.add_annotation(x=s['time'], y=s['price'], text="▲" if s['type']=="COMPRA" else "▼", color="green" if s['type']=="COMPRA" else "red", showarrow=True)

    fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # --- FOOTER: NOTICIAS Y REGISTRO ---
    c_n, c_h = st.columns(2)
    with c_n:
        st.subheader("📰 Noticias")
        feed = feedparser.parse("https://www.investing.com/rss/news_1.rss")
        for e in feed.entries[:3]: st.markdown(f"• [{e.title}]({e.link})")
    with c_h:
        st.subheader("📜 Historial de Sesión")
        if st.session_state.historial:
            st.dataframe(pd.DataFrame(st.session_state.historial).tail(5), use_container_width=True)
else:
    st.error("Esperando datos... Verifica la temporalidad.")
