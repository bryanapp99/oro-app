import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Bryan Gold 2026", layout="wide", page_icon="🔱")

# --- FUNCIÓN DE SONIDO ---
def play_notification_sound():
    # Sonido de notificación simple mediante HTML
    sound_html = """
    <audio autoplay>
    <source src="https://www.soundjay.com/buttons/beep-01a.mp3" type="audio/mpeg">
    </audio>
    """
    st.components.v1.html(sound_html, height=0)

# --- CONEXIÓN A GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Error: Configura la URL de Google Sheets en los Secrets de Streamlit.")

def cargar_historial():
    try:
        return conn.read(ttl=0).dropna(how="all")
    except:
        return pd.DataFrame(columns=["Fecha", "Hora", "Tipo", "Precio"])

def guardar_senal(tipo, precio):
    try:
        df_actual = cargar_historial()
        nueva_fila = pd.DataFrame([{
            "Fecha": datetime.now().strftime("%Y-%m-%d"),
            "Hora": datetime.now().strftime("%H:%M:%S"),
            "Tipo": tipo,
            "Precio": round(float(precio), 2)
        }])
        df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
        conn.update(data=df_final)
        st.toast(f"✅ Registrado en Google Sheets")
    except Exception as e:
        st.error(f"Error al guardar: {e}")

# --- OBTENCIÓN DE DATOS (XAUUSD - OANDA VIA YAHOO) ---
@st.cache_data(ttl=60)
def obtener_datos():
    try:
        # XAUUSD=X es el ticker de Yahoo para el Spot Gold (Oanda/Forex)
        ticker = "XAUUSD=X"
        data = yf.download(ticker, period="2d", interval="5m", progress=False)
        gold = yf.Ticker(ticker)
        return data, gold.news
    except:
        return pd.DataFrame(), []

# --- PROCESAMIENTO ---
df_raw, noticias_raw = obtener_datos()

if not df_raw.empty:
    # Ajuste de columnas para yfinance multi-index
    df = df_raw.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # 1. LÓGICA SCRIPT V6
    df['ema20'] = ta.ema(df['Close'], length=20)
    df['ema50'] = ta.ema(df['Close'], length=50)
    df['rsi'] = ta.rsi(df['Close'], length=14)
    
    # Velas Envolventes (Cierre[0] y Cierre[1])
    c = df['Close']
    o = df['Open']
    df['bullishEng'] = (c > o) & (c.shift(1) < o.shift(1)) & (c > o.shift(1))
    df['bearishEng'] = (c < o) & (c.shift(1) > o.shift(1)) & (c < o.shift(1))
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    precio_actual = float(last['Close'])
    
    # Condiciones de Señal
    es_compra = (last['ema20'] > last['ema50']) and last['bullishEng'] and (last['rsi'] < 65)
    es_venta = (last['ema20'] < last['ema50']) and last['bearishEng'] and (last['rsi'] > 35)

    # --- DISEÑO Bryan Gold 2026 ---
    st.title("🔱 Bryan Gold 2026 - OANDA Feed")
    
    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        # SECCIÓN 1: SEÑALES
        st.subheader("📡 Radar de Señales (Script V6)")
        
        if es_compra:
            st.success(f"### 🚀 SEÑAL DE COMPRA: {precio_actual:.2f}")
            play_notification_sound()
            if st.button("📥 GUARDAR COMPRA EN SHEETS"):
                guardar_senal("COMPRA 🟢", precio_actual)
        elif es_venta:
            st.error(f"### 🔥 SEÑAL DE VENTA: {precio_actual:.2f}")
            play_notification_sound()
            if st.button("📥 GUARDAR VENTA EN SHEETS"):
                guardar_senal("VENTA 🔴", precio_actual)
        else:
            st.info(f"🔎 Analizando mercado... | Precio actual: **{precio_actual:.2f}** | RSI: {last['rsi']:.2f}")

        # SECCIÓN 2: SIMULADOR DE RIESGO
        st.divider()
        st.subheader("🧮 Simulador de Riesgo & Niveles")
        s1, s2, s3 = st.columns(3)
        
        with s1:
            balance = st.number_input("Balance Cuenta ($)", value=1000.0, step=100.0)
            riesgo_pct = st.slider("Riesgo por operación %", 0.1, 5.0, 1.0)
        
        with s2:
            puntos_sl = st.number_input("Puntos de SL (Ej: 3)", value=3.0, step=0.1)
            puntos_tp = st.number_input("Puntos de TP (Ej: 4.5)", value=4.5, step=0.1)
            
        with s3:
            entrada_m = st.number_input("Precio Entrada", value=precio_actual)

        # Lógica de cálculo monetario
        es_short_calc = es_venta or (entrada_m < last['ema20'])
        sl_precio = entrada_m + puntos_sl if es_short_calc else entrada_m - puntos_sl
        tp_precio = entrada_m - puntos_tp if es_short_calc else entrada_m + puntos_tp
        
        riesgo_dinero = balance * (riesgo_pct / 100)
        ganancia_dinero = riesgo_dinero * (puntos_tp / puntos_sl)

        r1, r2, r3 = st.columns(3)
        r1.metric("🛡️ Stop Loss", f"{sl_precio:.2f}", f"-${riesgo_dinero:.2f}", delta_color="inverse")
        r2.metric("🎯 Take Profit", f"{tp_precio:.2f}", f"+${ganancia_dinero:.2f}")
        r3.metric("⚖️ Ratio R:R", f"1:{(puntos_tp/puntos_sl):.1f}")

        # SECCIÓN 4: REGISTRO HISTÓRICO
        st.divider()
        st.subheader("📜 Historial Registrado (Google Sheets)")
        historial_df = cargar_historial()
        if not historial_df.empty:
            st.dataframe(historial_df.iloc[::-1], use_container_width=True)

    with col_der:
        # SECCIÓN 3: NOTICIAS ORO & DÓLAR
        st.subheader("📰 Noticias Fundamentales")
        if noticias_raw:
            for n in noticias_
