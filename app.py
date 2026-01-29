import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# Configuración de página
st.set_page_config(page_title="Gold Master Pro V6", layout="centered")

# 1. FUNCIÓN DE CONEXIÓN ROBUSTA
def obtener_datos():
    # Intentamos primero con el Spot (Forex), si falla usamos el CFD de Oro
    for ticker in ["XAUUSD=X", "GOLD"]:
        try:
            gold = yf.Ticker(ticker)
            df = gold.history(period="1d", interval="5m")
            if not df.empty:
                return df, ticker
        except:
            continue
    return pd.DataFrame(), None

def procesar_datos(df):
    # EMAs
    df['ema20'] = ta.ema(df['Close'], length=20)
    df['ema50'] = ta.ema(df['Close'], length=50)
    # RSI
    df['rsi'] = ta.rsi(df['Close'], length=14)
    
    # Lógica de Velas Envolventes
    df['bull_eng'] = (df['Close'] > df['Open']) & (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Close'] > df['Open'].shift(1))
    df['bear_eng'] = (df['Close'] < df['Open']) & (df['Close'].shift(1) > df['Open'].shift(1)) & (df['Close'] < df['Open'].shift(1))
    
    # Señales finales
    df['compra'] = (df['ema20'] > df['ema50']) & df['bull_eng'] & (df['rsi'] < 65)
    df['venta'] = (df['ema20'] < df['ema50']) & df['bear_eng'] & (df['rsi'] > 35)
    
    return df.iloc[-1]

# --- INTERFAZ ---
st.header("🔱 Gold Master Pro V6 - Radar")

df, ticker_usado = obtener_datos()

if not df.empty:
    datos = procesar_datos(df)
    precio_actual = datos['Close']

    # --- CUADRO DE INDICACIÓN DE SEÑAL ---
    st.subheader("Indicación del Mercado")
    if datos['compra']:
        st.success(f"🚀 SEÑAL: COMPRA @ {precio_actual:.2f}")
        estado = "COMPRA"
    elif datos['venta']:
        st.error(f"🔥 SEÑAL: VENTA @ {precio_actual:.2f}")
        estado = "VENTA"
    else:
        st.info("⏳ BUSCANDO SEÑAL (Cumpliendo condiciones...)")
        estado = "ESPERA"

    st.divider()

    # --- SIMULADOR DE RIESGO ---
    st.subheader("Simulador de Riesgo y Gestión")
    col1, col2 = st.columns(2)
    
    with col1:
        balance = st.number_input("Balance de cuenta ($)", value=1000.0)
        riesgo_pct = st.slider("Riesgo por operación (%)", 0.5, 5.0, 1.0)
        entrada_manual = st.number_input("Precio de Entrada (Ajustar si es necesario)", value=precio_actual)

    # Lógica de TP/SL (3 puntos SL / 4.5 puntos TP)
    if estado == "VENTA":
        sl = entrada_manual + 3.0
        tp = entrada_manual - 4.5
    else:
        sl = entrada_manual - 3.0
        tp = entrada_manual + 4.5

    dinero_riesgo = balance * (riesgo_pct / 100)
    ganancia_posible = dinero_riesgo * 1.5

    with col2:
        st.metric("🎯 Take Profit", f"{tp:.2f}")
        st.metric("🛡️ Stop Loss", f"{sl:.2f}")

    st.divider()

    # --- REFERENCIA DE VALOR ---
    st.subheader("Proyección de la Operación")
    res1, res2 = st.columns(2)
    
    with res1:
        st.error(f"Pérdida si toca SL:\n\n**- ${dinero_riesgo:.2f}**")
        
    with res2:
        st.success(f"Ganancia si toca TP:\n\n**+ ${ganancia_posible:.2f}**")

    st.caption(f"Datos obtenidos de: {ticker_usado}")

else:
    st.error("❌ ERROR DE CONEXIÓN: No se pudieron obtener datos del mercado.")
    st.info("Yahoo Finance puede estar bloqueando la petición. Prueba pulsando el botón de abajo.")

if st.button("🔄 ACTUALIZAR"):
    st.rerun()
