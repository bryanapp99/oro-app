import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Bryan Gold 2026", layout="wide", page_icon="🔱")

# --- SONIDO DE NOTIFICACIÓN ---
def play_notification_sound():
    sound_html = """
    <audio autoplay><source src="https://www.soundjay.com/buttons/beep-01a.mp3" type="audio/mpeg"></audio>
    """
    st.components.v1.html(sound_html, height=0)

# --- CONEXIÓN A GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Error de conexión: Revisa los Secrets de Streamlit.")

def cargar_historial():
    try:
        # Forzamos la lectura fresca de la base de datos
        df_hist = conn.read(ttl=0)
        return df_hist.dropna(how="all")
    except:
        return pd.DataFrame(columns=["Fecha", "Hora", "Tipo", "Precio"])

def guardar_senal(tipo, precio):
    try:
        df_actual = cargar_historial()
        ahora = datetime.now()
        nueva_fila = pd.DataFrame([{
            "Fecha": ahora.strftime("%Y-%m-%d"),
            "Hora": ahora.strftime("%H:%M:%S"),
            "Tipo": tipo,
            "Precio": round(float(precio), 2)
        }])
        df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
        conn.update(data=df_final)
        st.toast(f"✅ Registrado en Google Sheets")
    except Exception as e:
        st.error(f"Error al guardar: {e}")

# --- OBTENCIÓN DE DATOS (XAUUSD - OANDA) ---
@st.cache_data(ttl=60)
def obtener_datos():
    try:
        # Ticker para Oro Spot (XAU/USD)
        ticker = "XAUUSD=X"
        data = yf.download(ticker, period="2d", interval="5m", progress=False)
        # Limpieza de columnas MultiIndex si existen
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        info_gold = yf.Ticker(ticker)
        noticias_feed = info_gold.news
        return data, noticias_feed
    except Exception as e:
        return pd.DataFrame(), []

# --- LÓGICA DE PROCESAMIENTO ---
df, noticias = obtener_datos()

if not df.empty:
    # Cálculos Técnicos (Pine Script v6)
    df['ema20'] = ta.ema(df['Close'], length=20)
    df['ema50'] = ta.ema(df['Close'], length=50)
    df['rsi'] = ta.rsi(df['Close'], length=14)
    
    # Velas Envolventes
    c = df['Close']
    o = df['Open']
    df['bullishEng'] = (c > o) & (c.shift(1) < o.shift(1)) & (c > o.shift(1))
    df['bearishEng'] = (c < o) & (c.shift(1) > o.shift(1)) & (c < o.shift(1))
    
    last = df.iloc[-1]
    precio_actual = float(last['Close'])
    
    # Condiciones de Señal Bryan Gold 2026
    es_compra = (last['ema20'] > last['ema50']) and last['bullishEng'] and (last['rsi'] < 65)
    es_venta = (last['ema20'] < last['ema50']) and last['bearishEng'] and (last['rsi'] > 35)

    # --- DISEÑO DE LA INTERFAZ ---
    st.title("🔱 Bryan Gold 2026")
    
    col_main, col_side = st.columns([2, 1])

    with col_main:
        # 1. SECCIÓN DE SEÑALES
        st.subheader("📡 Radar de Señales (Script V6)")
        if es_compra:
            st.success(f"### 🚀 COMPRA DETECTADA @ {precio_actual:.2f}")
            play_notification_sound()
            if st.button("📥 REGISTRAR COMPRA EN SHEETS"):
                guardar_senal("COMPRA 🟢", precio_actual)
        elif es_venta:
            st.error(f"### 🔥 VENTA DETECTADA @ {precio_actual:.2f}")
            play_notification_sound()
            if st.button("📥 REGISTRAR VENTA EN SHEETS"):
                guardar_senal("VENTA 🔴", precio_actual)
        else:
            st.info(f"🔎 Analizando... Precio: {precio_actual:.2f} | RSI: {last['rsi']:.1f}")

        # 2. SIMULADOR DE RIESGO
        st.divider()
        st.subheader("🧮 Simulador de Riesgo y Gestión")
        s1, s2, s3 = st.columns(3)
        with s1:
            balance = st.number_input("Balance Cuenta ($)", value=1000.0)
            riesgo_pct = st.slider("Riesgo %", 0.1, 5.0, 1.0)
        with s2:
            puntos_sl = st.number_input("Puntos Stop Loss", value=3.0)
            puntos_tp = st.number_input("Puntos Take Profit", value=4.5)
        with s3:
            entrada_m = st.number_input("Precio de Entrada", value=precio_actual)

        # Cálculo dinámico
        es_short = es_venta or (entrada_m < last['ema20'])
        sl_final = entrada_m + puntos_sl if es_short else entrada_m - puntos_sl
        tp_final = entrada_m - puntos_tp if es_short else entrada_m + puntos_tp
        
        perdida_usd = balance * (riesgo_pct / 100)
        ganancia_usd = perdida_usd * (puntos_tp / puntos_sl)

        m1, m2, m3 = st.columns(3)
        m1.metric("🛡️ SL Precio", f"{sl_final:.2f}", f"-${perdida_usd:.2f}", delta_color="inverse")
        m2.metric("🎯 TP Precio", f"{tp_final:.2f}", f"+${ganancia_usd:.2f}")
        m3.metric("⚖️ Ratio R:R", f"1:{(puntos_tp/puntos_sl):.1f}")

        # 4. REGISTRO GOOGLE SHEETS
        st.divider()
        st.subheader("📜 Historial en la Nube (Google Sheets)")
        historial_df = cargar_historial()
        if not historial_df.empty:
            st.dataframe(historial_df.iloc[::-1], use_container_width=True)
        else:
            st.write("Esperando primera señal para registrar...")

    with col_side:
        # 3. NOTICIAS
        st.subheader("📰 Noticias Oro & Dólar")
        if noticias:
            for n in noticias[:6]:
                titulo = n.get('title', 'Sin título')
                enlace = n.get('link', '#')
                resumen = n.get('summary', 'Click para ver más detalles...')
                fuente = n.get('publisher', 'Yahoo Finance')
                
                st.markdown(f"**[{titulo}]({enlace})**")
                st.write(f"{resumen[:130]}...")
                st.caption(f"Fuente: {fuente}")
                st.divider()
        else:
            st.write("Sin noticias relevantes en este momento.")

else:
    st.error("⚠️ Error obteniendo datos de OANDA. Reintenta en unos segundos.")

# BOTÓN ACTUALIZAR
if st.button("🔄 ACTUALIZAR TODO"):
    st.rerun()
