import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd  # <-- Esto era lo que faltaba

st.set_page_config(page_title="Gold Signal Pro", layout="centered")

st.markdown("<h1 style='text-align: center; color: #FFD700;'>🥇 XAU/USD PRO</h1>", unsafe_allow_html=True)

# 1. Obtener datos (Usamos el ticker del Oro en vivo)
# Como es domingo, pedimos 7 días para asegurar que cargue historial del viernes
data = yf.download("GC=F", interval="15m", period="7d")

if data.empty or len(data) < 20:
    st.error("⚠️ Esperando conexión con el mercado...")
    st.info("El mercado está abriendo. Refresca en unos minutos cuando haya más velas disponibles.")
else:
    # 2. Limpieza de datos (Manejo de columnas multi-index de yfinance)
    if isinstance(data.columns, pd.MultiIndex):
        close_prices = data['Close'].iloc[:, 0]
    else:
        close_prices = data['Close']
    
    # 3. Cálculo de indicadores con seguridad
    # Usamos una EMA de 50 para que sea más rápida y no pida tantas velas al inicio
    ema_trend = ta.ema(close_prices, length=50)
    rsi = ta.rsi(close_prices, length=14)
    
    current_price = float(close_prices.iloc[-1])
    current_ema = float(ema_trend.iloc[-1])
    current_rsi = float(rsi.iloc[-1])

    # 4. Interfaz Visual
    st.metric(label="Precio Actual XAU/USD", value=f"${current_price:,.2f}")
    
    col1, col2 = st.columns(2)
    col1.write(f"**EMA (Tendencia):** {current_ema:.2f}")
    col2.write(f"**RSI (Fuerza):** {current_rsi:.2f}")

    # Lógica de señales
    if current_price > current_ema and current_rsi < 45:
        st.success("🚀 SEÑAL: COMPRA (BUY)")
    elif current_price < current_ema and current_rsi > 55:
        st.error("🔥 SEÑAL: VENTA (SELL)")
    else:
        st.warning("⚖️ ESTADO: Buscando entrada...")

    st.write("---")
    st.line_chart(close_prices)
