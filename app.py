import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# Configuración de página
st.set_page_config(page_title="Gold Master Pro V6", layout="centered")

# 1. FUNCIÓN DE CÁLCULOS TÉCNICOS (Tu script de TV traducido)
def procesar_datos():
    # Obtenemos datos del Oro (XAUUSD)
    gold = yf.Ticker("XAUUSD=X") 
    df = gold.history(period="1d", interval="5m")
    
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
    
    return df.iloc[-1] # Solo nos interesa la vela actual

# --- INTERFAZ ---
st.header("🔱 Gold Master Pro V6 - Radar")

try:
    datos = procesar_datos()
    precio_actual = datos['Close']

    # --- CUADRO DE INDICACIÓN DE SEÑAL ---
    st.subheader("Indicación del Mercado")
    if datos['compra']:
        st.success(f"🚀 SEÑAL ACTUAL: COMPRA ENTRAR @ {precio_actual:.2f}")
        estado = "COMPRA"
    elif datos['venta']:
        st.error(f"🔥 SEÑAL ACTUAL: VENTA ENTRAR @ {precio_actual:.2f}")
        estado = "VENTA"
    else:
        st.info("⏳ BUSCANDO SEÑAL (Cumpliendo condiciones...)")
        estado = "ESPERA"

    st.divider()

    # --- SIMULADOR DE RIESGO Y VALORES ---
    st.subheader("Simulador de Riesgo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        balance = st.number_input("Balance de cuenta ($)", value=1000.0)
        riesgo_pct = st.slider("Riesgo por operación (%)", 0.5, 5.0, 1.0)
        entrada_manual = st.number_input("Precio de Entrada", value=precio_actual)

    # Cálculo de TP/SL basado en tu script (3 puntos SL / 4.5 puntos TP)
    if estado == "VENTA" or (estado == "ESPERA" and entrada_manual < precio_actual):
        sl = entrada_manual + 3.0
        tp = entrada_manual - 4.5
    else:
        sl = entrada_manual - 3.0
        tp = entrada_manual + 4.5

    # Cálculo de dinero a ganar o perder
    dinero_riesgo = balance * (riesgo_pct / 100)
    ganancia_posible = dinero_riesgo * 1.5 # Ratio 1.5 de tu script

    with col2:
        st.metric("🎯 Take Profit", f"{tp:.2f}")
        st.metric("🛡️ Stop Loss", f"{sl:.2f}")

    st.divider()

    # --- REFERENCIA DE VALOR A GANAR O PERDER ---
    st.subheader("Proyección de la Operación")
    res1, res2 = st.columns(2)
    
    with res1:
        st.error(f"Si toca Stop Loss perderás:\n\n**- ${dinero_riesgo:.2f}**")
        
    with res2:
        st.success(f"Si toca Take Profit ganarás:\n\n**+ ${ganancia_posible:.2f}**")

except Exception as e:
    st.warning("Conectando con el mercado... pulsa el botón para actualizar.")

if st.button("🔄 ACTUALIZAR PRECIO Y SEÑALES"):
    st.rerun()
