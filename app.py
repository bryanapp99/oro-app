import streamlit as st
import yfinance as yf
import pandas_ta as ta

st.set_page_config(page_title="Gold Signal Pro", layout="centered")

st.markdown("<h1 style='text-align: center; color: #FFD700;'>🥇 XAU/USD PRO</h1>", unsafe_allow_html=True)

# 1. Obtener datos (aumentamos el periodo a 5d para tener datos suficientes)
data = yf.download("GC=F", interval="15m", period="5d")

# 2. Verificar si hay datos antes de calcular
if data.empty or len(data) < 200:
    st.error("⚠️ No hay suficientes datos de mercado en este momento (posible cierre de fin de semana).")
    st.info("El mercado de oro abre los domingos a las 6:00 PM EST.")
else:
    # Seleccionamos la columna de cierre correctamente
    close_prices = data['Close'].iloc[:, 0] if isinstance(data['Close'], pd.DataFrame) else data['Close']
    
    # 3. Cálculo de indicadores
    ema_200 = ta.ema(close_prices, length=200).iloc[-1]
    rsi = ta.rsi(close_prices, length=14).iloc[-1]
    price = close_prices.iloc[-1]

    # 4. Diseño de la interfaz
    st.metric(label="Precio Actual Oro", value=f"${price:,.2f}")
    
    col1, col2 = st.columns(2)
    col1.write(f"**EMA 200:** {ema_200:.2f}")
    col2.write(f"**RSI:** {rsi:.2f}")

    if price > ema_200 and rsi < 40:
        st.success("🚀 SEÑAL: COMPRA (BUY)")
    elif price < ema_200 and rsi > 60:
        st.error("🔥 SEÑAL: VENTA (SELL)")
    else:
        st.warning("⚖️ ESPERAR: Buscando oportunidad...")

    st.write("---")
    st.line_chart(close_prices)
