import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Bryan Gold 2026", layout="wide")

# --- FUNCIONES DE SONIDO ---
def play_sound(type):
    # Genera un tono simple mediante HTML/JS
    sound_html = f"""
    <audio autoplay>
    <source src="https://{"www.soundjay.com/buttons/beep-01a.mp3" if type=="buy" else "https://www.soundjay.com/buttons/beep-02.mp3"}" type="audio/mpeg">
    </audio>
    """
    st.components.v1.html(sound_html, height=0)

# --- CONEXIÓN A GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.sidebar.error("Error en Secrets de Google Sheets.")

def cargar_historial():
    try:
        return conn.read(ttl=0).dropna(how="all")
    except:
        return pd.DataFrame(columns=["Fecha", "Hora", "Tipo", "Precio"])

def guardar_senal_cloud(tipo, precio):
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

# --- OBTENCIÓN DE DATOS (XAU/USD OANDA) ---
@st.cache_data(ttl=30)
def obtener_datos():
    try:
        # GC=F es el futuro del oro (más líquido), alternativamente XAUUSD=X
        ticker = "GC=F" 
        data = yf.download(ticker, period="2d", interval="5m", progress=False)
        gold = yf.Ticker(ticker)
        return data, gold.news
    except:
        return pd.DataFrame(), []

# --- LÓGICA DEL SCRIPT GOLD MASTER PRO V6 ---
df, noticias = obtener_datos()

if not df.empty:
    # Adaptar columnas de yfinance
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    
    # Cálculos según tu script Pine v6
    df['ema20'] = ta.ema(df['Close'], length=20)
    df['ema50'] = ta.ema(df['Close'], length=50)
    df['rsi'] = ta.rsi(df['Close'], length=14)
    
    # Velas Envolventes
    df['bullishEng'] = (df['Close'] > df['Open']) & (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Close'] > df['Open'].shift(1))
    df['bearishEng'] = (df['Close'] < df['Open']) & (df['Close'].shift(1) > df['Open'].shift(1)) & (df['Close'] < df['Open'].shift(1))
    
    last = df.iloc[-1]
    precio_actual = float(last['Close'])
    
    # Condiciones exactas de tu script
    es_compra = (last['ema20'] > last['ema50']) and last['bullishEng'] and (last['rsi'] < 65)
    es_venta = (last['ema20'] < last['ema50']) and last['bearishEng'] and (last['rsi'] > 35)

    # --- INTERFAZ Bryan Gold 2026 ---
    st.title("🔱 Bryan Gold 2026")
    
    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        # 1. SECCIÓN DE SEÑALES
        st.subheader("📡 Señales en Tiempo Real (Script V6)")
        if es_compra:
            st.success(f"### 🟢 COMPRA DETECTADA @ {precio_actual:.2f}")
            play_sound("buy")
            if st.button("📥 REGISTRAR COMPRA"):
                guardar_senal_cloud("COMPRA 🟢", precio_actual)
        elif es_venta:
            st.error(f"### 🔴 VENTA DETECTADA @ {precio_actual:.2f}")
            play_sound("sell")
            if st.button("📥 REGISTRAR VENTA"):
                guardar_senal_cloud("VENTA 🔴", precio_actual)
        else:
            st.info(f"⏳ Buscando señal... | Precio: {precio_actual:.2f} | RSI: {last['rsi']:.1f}")

        # 2. SIMULADOR DE RIESGO EDITABLE
        st.divider()
        st.subheader("🧮 Simulador de Riesgo y Gestión")
        c1, c2, c3 = st.columns(3)
        with c1:
            balance = st.number_input("Balance Cuenta ($)", value=1000.0)
            riesgo_pct = st.slider("Riesgo %", 0.5, 5.0, 1.0)
        with c2:
            puntos_sl = st.number_input("Puntos Stop Loss", value=3.0)
            puntos_tp = st.number_input("Puntos Take Profit", value=4.5)
        with c3:
            entrada = st.number_input("Entrada Manual", value=precio_actual)

        # Cálculos de Riesgo
        es_short_calc = es_venta or (entrada < last['ema20'])
        sl_final = entrada + puntos_sl if es_short_calc else entrada - puntos_sl
        tp_final = entrada - puntos_tp if es_short_calc else entrada + puntos_tp
        
        perdida_usd = balance * (riesgo_pct / 100)
        ganancia_usd = perdida_usd * (puntos_tp / puntos_sl)

        m1, m2, m3 = st.columns(3)
        m1.metric("🛡️ SL Precio", f"{sl_final:.2f}", f"-${perdida_usd:.2f}", delta_color="inverse")
        m2.metric("🎯 TP Precio", f"{tp_final:.2f}", f"+${ganancia_usd:.2f}")
        m3.metric("⚖️ Ratio R:R", f"1:{(puntos_tp/puntos_sl):.2f}")

        # 4. REGISTRO GOOGLE SHEETS
        st.divider()
        st.subheader("📜 Historial de Señales (Cloud)")
        historial = cargar_historial()
        st.dataframe(historial.iloc[::-1], use_container_width=True)

    with col_der:
        # 3. NOTICIAS ORO Y DÓLAR
        st.subheader("📰 Noticias Fundamentales")
        if noticias:
            for n in noticias[:8]:
                st.markdown(f"**[{n.get('title', 'Noticia')}]({n.get('link', '#')})**")
                st.caption(f"Fuente: {n.get('publisher', 'Yahoo Finance')}")
                st.divider()
        else:
            st.write("No hay noticias en este momento.")

else:
    st.error("Esperando conexión con XAUUSD de OANDA...")

if st.button("🔄 ACTUALIZAR"):
    st.rerun()
