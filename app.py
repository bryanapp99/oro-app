import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Gold Terminal Pro", layout="wide")

# Estilo de título
st.markdown("<h1 style='text-align: center; color: #FFD700;'>🥇 XAU/USD TERMINAL</h1>", unsafe_allow_html=True)

# 1. Obtener Datos
data = yf.download("GC=F", interval="15m", period="7d")

if data.empty or len(data) < 20:
    st.error("Esperando datos del mercado...")
else:
    # Limpieza de datos
    if isinstance(data.columns, pd.MultiIndex):
        df = data.copy()
        df.columns = data.columns.get_level_values(0)
    else:
        df = data

    # 2. Indicadores
    ema_20 = ta.ema(df['Close'], length=20)
    rsi = ta.rsi(df['Close'], length=14)
    
    current_price = float(df['Close'].iloc[-1])
    current_rsi = float(rsi.iloc[-1])
    current_ema = float(ema_20.iloc[-1])

    # --- SECCIÓN 1: CUADRO DE SEÑAL ---
    st.subheader("📢 Estado de la Señal")
    
    if current_price > current_ema and current_rsi < 45:
        signal_type = "COMPRA (BUY)"
        bg_color = "#28a745" # Verde
        tp_price = current_price + 5.0 # Objetivo de 50 pips
        sl_price = current_price - 3.0 # Riesgo de 30 pips
    elif current_price < current_ema and current_rsi > 55:
        signal_type = "VENTA (SELL)"
        bg_color = "#dc3545" # Rojo
        tp_price = current_price - 5.0
        sl_price = current_price + 3.0
    else:
        signal_type = "ESPERAR (WAIT)"
        bg_color = "#6c757d" # Gris
        tp_price, sl_price = 0, 0

    st.markdown(f"""
        <div style="background-color:{bg_color}; padding:20px; border-radius:10px; text-align:center;">
            <h2 style="color:white; margin:0;">{signal_type}</h2>
            <p style="color:white; font-size:20px; margin:0;">Precio: ${current_price:,.2f}</p>
        </div>
    """, unsafe_allow_html=True)

    # --- SECCIÓN 2: SIMULADOR DE OPERACIÓN ---
    st.write("---")
    st.subheader("🧮 Simulador de Gestión de Riesgo")
    
    col_cap, col_risk = st.columns(2)
    capital = col_cap.number_input("Capital en cuenta ($)", value=1000.0, step=100.0)
    riesgo_pct = col_risk.slider("% de Riesgo por operación", 0.5, 5.0, 1.0)
    
    dinero_en_riesgo = capital * (riesgo_pct / 100)
    
    if signal_type != "ESPERAR (WAIT)":
        st.info(f"Para esta operación arriesgarás: **${dinero_en_riesgo:.2f}**")
        c1, c2, c3 = st.columns(3)
        c1.metric("ENTRY", f"{current_price:.2f}")
        c2.metric("TAKE PROFIT", f"{tp_price:.2f}", delta=f"{(tp_price-current_price):.2f}")
        c3.metric("STOP LOSS", f"{sl_price:.2f}", delta=f"{(sl_price-current_price):.2f}", delta_color="inverse")
    else:
        st.write("Configura tu capital mientras esperas una señal clara.")

    # --- SECCIÓN 3: GRÁFICO DE VELAS ---
    st.write("---")
    st.subheader("📊 Gráfico de Velas Japonesas")
    
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name="Velas"
    )])
    
    # Añadir EMA al gráfico
    fig.add_trace(go.Scatter(x=df.index, y=ema_20, mode='lines', line=dict(color='yellow', width=1), name='EMA 20'))
    
    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=500,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)
