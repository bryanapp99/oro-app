import streamlit as st
from twelvedata import TDClient
import pandas as pd
import pandas_ta as ta

# --- CONFIGURACIÓN ---
# Tu API Key de Twelve Data ya integrada
API_KEY = "d884dbc9d72b4df7b7309a8eefb01cc6" 

st.set_page_config(page_title="Gold Master Pro V6", layout="centered")

def obtener_datos():
    try:
        td = TDClient(apikey=API_KEY)
        # Obtenemos el Oro contra el Dólar (XAU/USD)
        ts = td.time_series(symbol="XAU/USD", interval="5min", outputsize=50)
        df = ts.as_pandas()
        # Ordenamos de más antigua a más reciente para los indicadores
        df = df.sort_index(ascending=True)
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

# --- INTERFAZ ---
st.title("🔱 Radar Gold Master Pro V6")

df = obtener_datos()

if not df.empty:
    # 1. CÁLCULOS TÉCNICOS (Lógica de tu Script de TradingView)
    df['ema20'] = ta.ema(df['close'], length=20)
    df['ema50'] = ta.ema(df['close'], length=50)
    df['rsi'] = ta.rsi(df['close'], length=14)
    
    # Lógica de Velas Envolventes (Price Action)
    df['bull_eng'] = (df['close'] > df['open']) & (df['close'].shift(1) < df['open'].shift(1)) & (df['close'] > df['open'].shift(1))
    df['bear_eng'] = (df['close'] < df['open']) & (df['close'].shift(1) > df['open'].shift(1)) & (df['close'] < df['open'].shift(1))
    
    # Capturamos la última vela cerrada
    last_row = df.iloc[-1]
    precio_actual = last_row['close']
    
    # Condiciones de Señal
    es_compra = (last_row['ema20'] > last_row['ema50']) and last_row['bull_eng'] and (last_row['rsi'] < 65)
    es_venta = (last_row['ema20'] < last_row['ema50']) and last_row['bear_eng'] and (last_row['rsi'] > 35)

    # --- 2. CUADRO DE INDICACIÓN DE SEÑAL ---
    st.subheader("📡 Indicación del Mercado")
    if es_compra:
        st.success(f"🚀 SEÑAL DETECTADA: COMPRA @ {precio_actual:.2f}")
        estado = "COMPRA"
    elif es_venta:
        st.error(f"🔥 SEÑAL DETECTADA: VENTA @ {precio_actual:.2f}")
        estado = "VENTA"
    else:
        st.info("⏳ BUSCANDO SEÑAL (Sin condiciones activas en este momento)")
        estado = "ESPERA"

    st.divider()

    # --- 3. SIMULADOR DE RIESGO ---
    st.subheader("🧮 Gestión de Riesgo y Niveles")
    col1, col2 = st.columns(2)
    
    with col1:
        balance = st.number_input("Balance de cuenta ($)", value=1000.0, step=100.0)
        riesgo_pct = st.slider("Riesgo por operación (%)", 0.5, 5.0, 1.0)
        precio_entrada = st.number_input("Precio de Entrada (Ajustar si es necesario)", value=precio_actual)

    # Lógica de TP y SL automática (3 puntos SL / 4.5 puntos TP)
    if es_venta or (estado == "ESPERA" and precio_entrada < last_row['ema20']):
        sl = precio_entrada + 3.0
        tp = precio_entrada - 4.5
    else:
        sl = precio_entrada - 3.0
        tp = precio_entrada + 4.5

    with col2:
        st.metric("🎯 Take Profit (TP)", f"{tp:.2f}")
        st.metric("🛡️ Stop Loss (SL)", f"{sl:.2f}")

    # --- 4. VALORES MONETARIOS ---
    st.divider()
    st.subheader("💰 Proyección de Ganancia / Pérdida")
    
    dinero_riesgo = balance * (riesgo_pct / 100)
    ganancia_esperada = dinero_riesgo * 1.5 # Ratio de riesgo 1:1.5

    res1, res2 = st.columns(2)
    with res1:
        st.error(f"Pérdida si toca SL:\n\n**- ${dinero_riesgo:.2f}**")
    with res2:
        st.success(f"Ganancia si toca TP:\n\n**+ ${ganancia_esperada:.2f}**")

    st.caption("Los datos se actualizan cada vez que presionas el botón.")

else:
    st.error("No se pudo conectar con el mercado. Revisa tu conexión o el estado de tu API Key.")

if st.button("🔄 ACTUALIZAR PRECIOS"):
    st.rerun()
