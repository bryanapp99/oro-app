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
    st.error("Error: Revisa los Secrets de Streamlit para la URL de Google Sheets.")

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

# --- OBTENCIÓN DE DATOS (XAUUSD - OANDA) ---
@st.cache_data(ttl=60)
def obtener_datos():
    try:
        ticker = "XAUUSD=X"
        data = yf.download(ticker, period="2d", interval="5m", progress=False)
        gold = yf.Ticker(ticker)
        return data, gold.news
    except:
        return pd.DataFrame(), []

# --- PROCESAMIENTO ---
df_raw, noticias = obtener_datos()

if not df_raw.empty:
    df = df_raw.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # LÓGICA SCRIPT V6
    df['ema20'] = ta.ema(df['Close'], length=20)
    df['ema50'] = ta.ema(df['Close'], length=50)
    df['rsi'] = ta.rsi(df['Close'], length=14)
    
    # Velas Envolventes
    c, o = df['Close'], df['Open']
    df['bullishEng'] = (c > o) & (c.shift(1) < o.shift(1)) & (c > o.shift(1))
    df['bearishEng'] = (c < o) & (c.shift(1) > o.shift(1)) & (c < o.shift(1))
    
    last = df.iloc[-1]
    precio_actual = float(last['Close'])
    
    # Condiciones
    es_compra = (last['ema20'] > last['ema50']) and last['bullishEng'] and (last['rsi'] < 65)
    es_venta = (last['ema20'] < last['ema50']) and last['bearishEng'] and (last['rsi'] > 35)

    # --- INTERFAZ ---
    st.title("🔱 Bryan Gold 2026")
    
    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        st.subheader("📡 Radar de Señales (OANDA)")
        if es_compra:
            st.success(f"### 🚀 COMPRA: {precio_actual:.2f}")
            play_notification_sound()
            if st.button("📥 GUARDAR COMPRA"): guardar_senal("COMPRA 🟢", precio_actual)
        elif es_venta:
            st.error(f"### 🔥 VENTA: {precio_actual:.2f}")
            play_notification_sound()
            if st.button("📥 GUARDAR VENTA"): guardar_senal("VENTA 🔴", precio_actual)
        else:
            st.info(f"🔎 Analizando... Precio: {precio_actual:.2f} | RSI: {last['rsi']:.1f}")

        # SIMULADOR DE RIESGO
        st.divider()
        st.subheader("🧮 Simulador de Riesgo")
        s1, s2, s3 = st.columns(3)
        with s1:
            balance = st.number_input("Balance ($)", value=1000.0)
            riesgo_pct = st.slider("Riesgo %", 0.1, 5.0, 1.0)
        with s2:
            puntos_sl = st.number_input("Puntos SL", value=3.0)
            puntos_tp = st.number_input("Puntos TP", value=4.5)
        with s3:
            entrada = st.number_input("Entrada", value=precio_actual)

        es_short = es_venta or (entrada < last['ema20'])
        sl = entrada + puntos_sl if es_short else entrada - puntos_sl
        tp = entrada - puntos_tp if es_short else entrada + puntos_tp
        
        r_dinero = balance * (riesgo_pct / 100)
        g_dinero = r_dinero * (puntos_tp / puntos_sl)

        m1, m2, m3 = st.columns(3)
        m1.metric("🛡️ SL", f"{sl:.2f}", f"-${r_dinero:.2f}", delta_color="inverse")
        m2.metric("🎯 TP", f"{tp:.2f}", f"+${g_dinero:.2f}")
        m3.metric("⚖️ Ratio", f"1:{(puntos_tp/puntos_sl):.1f}")

        st.divider()
        st.subheader("📜 Historial Google Sheets")
        st.dataframe(cargar_historial().iloc[::-1], use_container_width=True)

    with col_der:
        st.subheader("📰 Noticias & Resumen")
        if noticias:
            for n in noticias[:6]:
                st.markdown(f"**{n.get('title')}**")
                # Resumen breve
                resumen = n.get('summary', 'Click para ver más...')
                st.write(f"{resumen[:120]}...")
                st.markdown(f"[Fuente Completa]({n.get('link')})")
                st.divider()
        else:
            st.write("Sin noticias recientes.")

else:
    st.error("Error al obtener datos. Reintenta en un minuto.")

if st.button("🔄 ACTUALIZAR"):
    st.rerun()
