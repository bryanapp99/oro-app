import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
import feedparser
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Gold Master Pro", layout="wide")
if 'historial' not in st.session_state:
    st.session_state.historial = []

st_autorefresh(interval=60000, limit=1000, key="gold_sync_update")

# --- AJUSTES ---
st.sidebar.header("⚙️ Configuración")
intervalo = st.sidebar.selectbox("Temporalidad:", options=["1m", "5m", "15m", "1h", "1d"], index=2)
periodo_map = {"1m": "1d", "5m": "5d", "15m": "7d", "1h": "1mo", "1d": "6mo"}
distancia_sl = st.sidebar.slider("Distancia SL ($)", 1.0, 10.0, 3.0)

# --- DATOS ---
data = yf.download("GC=F", interval=intervalo, period=periodo_map[intervalo])

if not data.empty and len(data) > 50:
    df = data.copy()
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # Indicadores (Idénticos a Pine Script)
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    df['EMA_50'] = ta.ema(df['Close'], length=50)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    # Lógica de Velas Envolventes
    df['Bull_Eng'] = (df['Close'] > df['Open']) & (df['Close'].shift(1) < df['Open'].shift(1)) & \
                     (df['Close'] > df['Open'].shift(1)) & (df['Open'] < df['Close'].shift(1))
    
    df['Bear_Eng'] = (df['Close'] < df['Open']) & (df['Close'].shift(1) > df['Open'].shift(1)) & \
                     (df['Close'] < df['Open'].shift(1)) & (df['Open'] > df['Close'].shift(1))

    # Analizar última vela cerrada (shift 1 para estabilidad)
    last_row = df.iloc[-1]
    cp = float(last_row['Close'])
    
    signal = "ESPERAR"
    tp, sl = 0.0, 0.0

    if last_row['EMA_20'] > last_row['EMA_50'] and last_row['Bull_Eng'] and last_row['RSI'] < 65:
        signal = "COMPRA"
        sl = float(last_row['Low']) - distancia_sl
        tp = cp + (cp - sl) * 1.5
    elif last_row['EMA_20'] < last_row['EMA_50'] and last_row['Bear_Eng'] and last_row['RSI'] > 35:
        signal = "VENTA"
        sl = float(last_row['High']) + distancia_sl
        tp = cp - (sl - cp) * 1.5

    # Guardar en Historial
    if signal != "ESPERAR":
        if not st.session_state.historial or st.session_state.historial[-1]['time'] != df.index[-1]:
            st.session_state.historial.append({"time": df.index[-1], "price": cp, "type": signal, "tp": tp, "sl": sl})

    # --- INTERFAZ ---
    st.markdown("<h1 style='text-align: center; color: #FFD700;'>🥇 GOLD MASTER TERMINAL</h1>", unsafe_allow_html=True)
    
    col_sig, col_calc = st.columns(2)
    with col_sig:
        color = "#28a745" if signal == "COMPRA" else "#dc3545" if signal == "VENTA" else "#6c757d"
        st.markdown(f"<div style='background:{color};padding:20px;border-radius:10px;text-align:center;color:white'><h1>{signal}</h1><h3>${cp:,.2f}</h3></div>", unsafe_allow_html=True)

    with col_calc:
        if signal != "ESPERAR":
            st.metric("🎯 TAKE PROFIT", f"${tp:.2f}")
            st.metric("🛑 STOP LOSS", f"${sl:.2f}")
        else:
            st.info("Esperando confluencia de EMA 20/50 + Vela Envolvente...")

    # --- GRÁFICO CON PROYECCIÓN ---
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Velas")])
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], line=dict(color='orange', width=1.5), name='EMA 20'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='blue', width=1.5), name='EMA 50'))

    # Dibujar historial con TP/SL visual
    for s in st.session_state.historial:
        # Flecha de entrada
        fig.add_annotation(x=s['time'], y=s['price'], text="B" if s['type']=="COMPRA" else "S", bgcolor="green" if s['type']=="COMPRA" else "red", font=dict(color="white"))
        # Líneas de TP y SL
        fig.add_shape(type="line", x0=s['time'], y0=s['tp'], x1=df.index[-1], y1=s['tp'], line=dict(color="green", width=1, dash="dash"))
        fig.add_shape(type="line", x0=s['time'], y0=s['sl'], x1=df.index[-1], y1=s['sl'], line=dict(color="red", width=1, dash="dash"))

    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Mercado cerrado o insuficientes datos para esta temporalidad.")
