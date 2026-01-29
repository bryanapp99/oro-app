import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gold Master Pro V6 - Elite", layout="wide")

# --- FUNCIONES DE DATOS ---
@st.cache_data(ttl=60)
def obtener_datos_mercado():
    try:
        gold = yf.Ticker("GC=F")
        df = gold.history(period="1d", interval="5m")
        # Extraer noticias del ticker
        noticias = gold.news[:5] # Tomamos las últimas 5
        return df, noticias
    except:
        return pd.DataFrame(), []

# Inicializar historial en el estado de la sesión
if 'historial' not in st.session_state:
    st.session_state.historial = []

# --- INTERFAZ PRINCIPAL ---
st.title("🔱 Gold Master Pro V6 - Elite Radar")

df, noticias = obtener_datos_mercado()

if not df.empty:
    # CÁLCULOS TÉCNICOS
    df['ema20'] = ta.ema(df['Close'], length=20)
    df['ema50'] = ta.ema(df['Close'], length=50)
    df['rsi'] = ta.rsi(df['Close'], length=14)
    
    # Velas Envolventes
    bull_eng = (df['Close'] > df['Open']) & (df['Close'].shift(1) < df['Open'].shift(1))
    bear_eng = (df['Close'] < df['Open']) & (df['Close'].shift(1) > df['Open'].shift(1))
    
    last_row = df.iloc[-1]
    precio_actual = last_row['Close']
    
    # Lógica de Señales
    es_compra = (last_row['ema20'] > last_row['ema50']) and bull_eng.iloc[-1] and (last_row['rsi'] < 65)
    es_venta = (last_row['ema20'] < last_row['ema50']) and bear_eng.iloc[-1] and (last_row['rsi'] > 35)

    # Registrar señal si ocurre
    if es_compra or es_venta:
        nueva_señal = {
            "Hora": datetime.now().strftime("%H:%M:%S"),
            "Tipo": "COMPRA 🟢" if es_compra else "VENTA 🔴",
            "Precio": round(precio_actual, 2)
        }
        # Evitar duplicados en la misma vela
        if not st.session_state.historial or st.session_state.historial[-1]["Hora"][:-3] != nueva_señal["Hora"][:-3]:
            st.session_state.historial.append(nueva_señal)

    # --- LAYOUT DE 3 COLUMNAS ---
    col_main, col_side = st.columns([2, 1])

    with col_main:
        st.subheader("📡 Radar de Señales")
        if es_compra:
            st.success(f"🔥 SEÑAL ACTIVA: COMPRA @ {precio_actual:.2f}")
        elif es_venta:
            st.error(f"🔥 SEÑAL ACTIVA: VENTA @ {precio_actual:.2f}")
        else:
            st.info(f"⏳ Buscando Oportunidades... | RSI: {last_row['rsi']:.2f}")

        # --- AJUSTES DE SL/TP Y RIESGO ---
        st.divider()
        st.subheader("🧮 Configuración de Operación")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            balance = st.number_input("Balance ($)", value=1000.0)
            riesgo_pct = st.slider("Riesgo %", 0.1, 5.0, 1.0)
        
        with c2:
            puntos_sl = st.number_input("Puntos de SL", value=3.0, step=0.5)
            puntos_tp = st.number_input("Puntos de TP", value=4.5, step=0.5)
            
        with c3:
            entrada_manual = st.number_input("Precio Entrada", value=float(precio_actual))

        # Cálculos de Niveles
        es_short = es_venta or (entrada_manual < last_row['ema20'])
        sl_final = entrada_manual + puntos_sl if es_short else entrada_manual - puntos_sl
        tp_final = entrada_manual - puntos_tp if es_short else entrada_manual + puntos_tp
        
        dinero_riesgo = balance * (riesgo_pct / 100)
        ratio_rr = puntos_tp / puntos_sl
        ganancia_dinero = dinero_riesgo * ratio_rr

        # --- RESULTADOS ---
        res1, res2, res3 = st.columns(3)
        res1.metric("🛡️ Stop Loss", f"{sl_final:.2f}")
        res2.metric("🎯 Take Profit", f"{tp_final:.2f}")
        res3.metric("⚖️ Ratio R:R", f"1:{ratio_rr:.1f}")

        st.warning(f"Riesgo: -${dinero_riesgo:.2f} | Ganancia Potencial: +${ganancia_dinero:.2f}")

        # --- REGISTRO DE SEÑALES ---
        st.divider()
        st.subheader("📜 Registro de Señales (Sesión Actual)")
        if st.session_state.historial:
            st.table(pd.DataFrame(st.session_state.historial).iloc[::-1]) # Mostrar más reciente arriba
        else:
            st.write("No se han detectado señales todavía.")

    with col_side:
        st.subheader("📰 Noticias del Oro")
        if noticias:
            for n in noticias:
                st.markdown(f"**[{n['title']}]({n['link']})**")
                st.caption(f"Fuente: {n['publisher']}")
                st.divider()
        else:
            st.write("Cargando noticias...")

else:
    st.error("Error al conectar con el mercado. Reintenta en unos segundos.")

if st.button("🔄 Sincronizar Todo"):
    st.rerun()
