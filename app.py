import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
import feedparser
from streamlit_autorefresh import st_autorefresh

# 1. Configuración de Página y Memoria
st.set_page_config(page_title="Gold Terminal PRO", layout="wide")
if 'historial' not in st.session_state:
    st.session_state.historial = []

# Autorefresh cada 60 segundos
st_autorefresh(interval=60000, limit=1000, key="gold_update_final")

# 2. Barra Lateral (Configuración)
st.sidebar.header("⚙️ Ajustes")
intervalo = st.sidebar.selectbox("Temporalidad:", options=["1m", "5m", "15m", "1h", "1d"], index=2)
periodo_map = {"1m": "1d", "5m": "5d", "15m": "7d", "1h": "1mo", "1d": "6mo"}
periodo = periodo_map[intervalo]

# 3. Función de Sonido
def play_alert():
    audio_html = """<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg"></audio>"""
    st.components.v1.html(audio_html, height=0)

# 4. Obtención de Datos
data = yf.download("GC=F", interval=intervalo, period=periodo)

if not data.empty and len(data) > 20:
    df = data.copy()
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # Indicadores
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    current_p = float(df['Close'].iloc[-1])
    current_rsi = float(df['RSI'].iloc[-1])
    current_ema = float(df['EMA_20'].iloc[-1])
    current_time = df.index[-1]

    # Lógica de Señal
    signal = "ESPERAR"
    if current_p > current_ema and current_rsi < 45: signal = "COMPRA"
    elif current_p < current_ema and current_rsi > 55: signal = "VENTA"

    # Guardar en Historial y Sonar
    if signal != "ESPERAR":
        if not st.session_state.historial or st.session_state.historial[-1]['time'] != current_time:
            st.session_state.historial.append({"time": current_time, "price": current_p, "type": signal})
            play_alert()

    # --- DISEÑO DE INTERFAZ ---
    st.markdown(f"<h1 style='text-align: center; color: #FFD700;'>🥇 GOLD TERMINAL PRO</h1>", unsafe_allow_html=True)
    
    # Fila Superior: Señal y Simulador
    col_sig, col_calc = st.columns([1, 1])

    with col_sig:
        st.subheader("📢 Señal en Vivo")
        color = "#28a745" if signal == "COMPRA" else "#dc3545" if signal == "VENTA" else "#6c757d"
        st.markdown(f"<div style='background:{color};padding:20px;border-radius:10px;text-align:center;color:white'><h1>{signal}</h1><p style='font-size:25px;'>${current_p:,.2f}</p></div>", unsafe_allow_html=True)

    with col_calc:
        st.subheader("🧮 Gestión de Riesgo")
        cap = st.number_input("Capital ($)", value=1000.0)
        riesgo = st.slider("% Riesgo", 0.5, 5.0, 1.0)
        st.info(f"Riesgo: **${(cap * (riesgo/100)):.2f}**")
        if signal != "ESPERAR":
            tp = current_p + 5.0 if signal == "COMPRA" else current_p - 5.0
            sl = current_p - 3.0 if signal == "COMPRA" else current_p + 3.0
            st.success(f"🎯 TP: {tp:.2f} | 🛑 SL: {sl:.2f}")

    # --- GRÁFICO CON FLECHAS ---
    st.write("---")
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="XAU/USD")])
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], line=dict(color='yellow', width=1.5), name='Trend'))
    
    # Dibujar flechas del historial
    for s in st.session_state.historial:
        color_f = "#28a745" if s['type'] == "COMPRA" else "#dc3545"
        fig.add_annotation(x=s['time'], y=s['price'], text=f"{s['type']}", showarrow=True, arrowhead=2, bgcolor=color_f, font=dict(color="white"))

    fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # --- NOTICIAS Y REGISTRO ---
    c_n, c_h = st.columns(2)
    with c_n:
        st.subheader("📰 Noticias")
        feed = feedparser.parse("https://www.investing.com/rss/news_1.rss")
        for e in feed.entries[:3]: st.markdown(f"• [{e.title}]({e.link})")
    with c_h:
        st.subheader("📜 Historial Hoy")
        if st.session_state.historial:
            st.table(pd.DataFrame(st.session_state.historial).tail(5))

else:
    st.warning("Buscando conexión con el mercado...")
    import gspread
from google.oauth2.service_account import Credentials

# Esto se conecta a tu Google Sheets
def guardar_senal_en_nube(tiempo, precio, tipo):
    # Aquí conectaríamos tus credenciales de Google
    # Cada vez que 'signal' cambie, enviamos una fila nueva
    pass
