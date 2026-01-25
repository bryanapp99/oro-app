import streamlit as st
import yfinance as yf
import pandas_ta as ta

st.set_page_config(page_title="Gold Signal Pro", layout="centered")

st.markdown("<h1 style='text-align: center; color: #FFD700;'>🥇 XAU/USD PRO</h1>", unsafe_allow_html=True)

# Obtener datos del oro
data = yf.download("GC=F", interval="15m", period="2d")
if not data.empty:
    price = data['Close'].iloc[-1]
    # Cálculo de indicadores
    ema_200 = ta.ema(data['Close'], length=200).iloc[-1]
    rsi = ta.rsi(data['Close'], length=14).iloc[-1]

    # Diseño de la señal
    st.metric(label="Precio Actual Oro", value=f"${price:,.2f}")
    
    if price > ema_200 and rsi < 40:
        st.success("🚀 SEÑAL: COMPRA (BUY)")
        st.info("Confluencia: Tendencia Alcista + RSI en Descuento")
    elif price < ema_200 and rsi > 60:
        st.error("🔥 SEÑAL: VENTA (SELL)")
        st.info("Confluencia: Tendencia Bajista + RSI en Sobrecompra")
    else:
        st.warning("⚖️ ESPERAR: Buscando oportunidad...")

    st.write("---")
    st.line_chart(data['Close'])
