import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
import feedparser
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Gold Terminal Elite", layout="wide")
st_autorefresh(interval=60000, limit=1000, key="gold_update")

# --- 1. MEMORIA DE SEÑALES (HISTORIAL) ---
if 'historial_senales' not in st.session_state:
    st.session_state.historial_senales = []

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Configuración")
intervalo = st.sidebar.selectbox("Temporalidad:", options=["1m", "5m", "15m", "1h", "1d"], index=2)

# --- OBTENER DATOS ---
data = yf.download("GC=F", interval=intervalo, period="7d")

if not data.empty and len(data) > 20:
    df = data.copy()
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # Indicadores
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    current_time = df.index[-1]
    current_price = float(df['Close'].iloc[-1])
    current_rsi = float(df['RSI'].iloc[-1])
    current_ema = float(df['EMA_20'].iloc[-1])

    # --- LÓGICA DE SEÑAL ---
    signal = "ESPERAR"
    if current_price > current_ema and current_rsi < 45:
        signal = "COMPRA"
    elif current_price < current_ema and current_rsi > 55:
        signal = "VENTA"

    # Guardar en el historial si la señal es nueva para este timestamp
    if signal != "ESPERAR":
        nueva_entrada = {"time": current_time, "price": current_price, "type": signal}
        # Evitar duplicados en la misma vela
        if not st.session_state.historial_senales or st.session_state.historial_senales[-1]['time'] != current_time:
            st.session_state.historial_senales.append(nueva_entrada)

    # --- INTERFAZ ---
    st.markdown(f"<h1 style='text-align: center; color: #FFD700;'>🥇 XAU/USD PRO TERMINAL</h1>", unsafe_allow_html=True)
    
    col_sig, col_calc = st.columns(2)
    with col_sig:
        color = "#28a745" if signal == "COMPRA" else "#dc3545" if signal == "VENTA" else "#6c757d"
        st.markdown(f"<div style='background:{color};padding:10px;border-radius:5px;text-align:center;color:white'><h2>{signal}</h2></div>", unsafe_allow_html=True)
    
    # --- GRÁFICO CON FLECHAS ---
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Precio")])
    
    # Agregar Flechas del Historial
    for s in st.session_state.historial_senales:
        if s['type'] == "COMPRA":
            fig.add_annotation(x=s['time'], y=df.loc[s['time']]['Low'], text="▲ BUY", showarrow=True, arrowhead=1, bgcolor="#28a745", font=dict(color="white"))
        else:
            fig.add_annotation(x=s['time'], y=df.loc[s['time']]['High'], text="▼ SELL", showarrow=True, arrowhead=1, bgcolor="#dc3545", font=dict(color="white"), ay=-40)

    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # --- TABLA DE REGISTRO ---
    with st.expander("📜 Ver Registro Histórico de Señales"):
        if st.session_state.historial_senales:
            hist_df = pd.DataFrame(st.session_state.historial_senales)
            st.table(hist_df.tail(10)) # Mostrar últimas 10
        else:
            st.write("Aún no se han detectado señales en esta sesión.")
