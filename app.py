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
    sound_html = """<audio autoplay><source src="https://www.soundjay.com/buttons/beep-01a.mp3" type="audio/mpeg"></audio>"""
    st.components.v1.html(sound_html, height=0)

# --- CONEXIÓN A GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Error: Revisa los Secrets de Streamlit.")

def cargar_historial():
    try:
        return conn.read(ttl=0).dropna(how="all")
    except:
        return pd.DataFrame(columns=["Fecha", "Hora", "Tipo", "Precio"])

def guardar_senal(tipo, precio):
    try:
        df_actual = cargar_historial()
        nueva_fila = pd.DataFrame([{"Fecha": datetime.now().strftime("%Y-%m-%d"), "Hora": datetime.now().strftime("%H:%M:%S"), "Tipo": tipo, "Precio": round(float(precio), 2)}])
        df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
        conn.update(data=df_final)
        st.toast(f"✅ Registrado en Google Sheets")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Error al guardar: {e}")

# --- OBTENCIÓN DE DATOS Y NOTICIAS ---
@st.cache_data(ttl=60)
def obtener_todo():
    ticker = "XAUUSD=X"
    try:
        # Descarga de precios
        data = yf.download(ticker, period="3d", interval="5m", progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        # Descarga de noticias
        gold_obj = yf.Ticker(ticker)
        news = gold_obj.news
        return data, news, ticker
    except:
        return pd.DataFrame(), [], None

# --- EJECUCIÓN ---
df, noticias, ticker_activo = obtener_todo()

if not df.empty:
    # Lógica Script V6
    df['ema20'] = ta.ema(df['Close'], length=20)
    df['ema50'] = ta.ema(df['Close'], length=50)
    df['rsi'] = ta.rsi(df['Close'], length=14)
    c, o = df['Close'], df['Open']
    df['bullishEng'] = (c > o) & (c.shift(1) < o.shift(1)) & (c > o.shift(1))
    df['bearishEng'] = (c < o) & (c.shift(1) > o.shift(1)) & (c < o.shift(1))
    
    last = df.iloc[-1]
    precio_actual = float(last['Close'])
    es_compra = (last['ema20'] > last['ema50']) and last['bullishEng'] and (last['rsi'] < 65)
    es_venta = (last['ema20'] < last['ema50']) and last['bearishEng'] and (last['rsi'] > 35)

    st.title("🔱 Bryan Gold 2026")
    col_izq, col_der = st.columns([2, 1]) # Usamos col_der aquí

    with col_izq:
        st.subheader("📡 Radar de Señales (OANDA Feed)")
        if es_compra:
            st.success(f"### 🚀 SEÑAL DE COMPRA: {precio_actual:.2f}")
            play_notification_sound()
            if st.button("📥 GUARDAR COMPRA"): guardar_senal("COMPRA 🟢", precio_actual)
        elif es_venta:
            st.error(f"### 🔥 SEÑAL DE VENTA: {precio_actual:.2f}")
            play_notification_sound()
            if st.button("📥 GUARDAR VENTA"): guardar_senal("VENTA 🔴", precio_actual)
        else:
            st.info(f"🔎 Analizando... Precio: **{precio_actual:.2f}** | RSI: {last['rsi']:.1f}")

        st.divider()
        st.subheader("🧮 Simulador de Riesgo")
        s1, s2, s3 = st.columns(3)
        with s1:
            balance = st.number_input("Balance ($)", value=1000.0)
            riesgo_pct = st.slider("Riesgo %", 0.1, 5.0, 1.0)
        with s2:
            puntos_sl, puntos_tp = st.number_input("Puntos SL", value=3.0), st.number_input("Puntos TP", value=4.5)
        with s3:
            entrada = st.number_input("Entrada Manual", value=precio_actual)

        es_short = es_venta or (entrada < last['ema20'])
        sl = entrada + puntos_sl if es_short else entrada - puntos_sl
        tp = entrada - puntos_tp if es_short else entrada + puntos_tp
        r_usd, g_usd = balance * (riesgo_pct/100), (balance * (riesgo_pct/100)) * (puntos_tp/puntos_sl)

        m1, m2, m3 = st.columns(3)
        m1.metric("🛡️ SL", f"{sl:.2f}", f"-${r_usd:.2f}", delta_color="inverse")
        m2.metric("🎯 TP", f"{tp:.2f}", f"+${g_usd:.2f}")
        m3.metric("⚖️ Ratio R:R", f"1:{(puntos_tp/puntos_sl):.1f}")

        st.divider()
        st.subheader("📜 Historial Google Sheets")
        st.dataframe(cargar_historial().iloc[::-1], use_container_width=True)

    with col_der: # Corregido: antes decía col_side
        st.subheader("📰 Noticias del Oro y Dólar")
        
        # Bloque de noticias en vivo
        if noticias:
            for n in noticias[:5]: # Mostramos las 5 más recientes
                st.markdown(f"**[{n.get('title')}]({n.get('link')})**")
                st.caption(f"Fuente: {n.get('publisher')} | [Ver noticia]({n.get('link')})")
                st.divider()
        else:
            st.warning("No se detectan noticias automáticas en este momento.")
            
        # Bloque de respaldo (Noticias fijas de alto impacto hoy)
        st.info("**ANÁLISIS DE HOY 28-JAN-2026**")
        st.markdown("""
        * **FED:** El mercado espera la decisión de tipos hoy. Volatilidad alta.
        * **Dólar (DXY):** Manteniéndose estable en la zona de 103.50.
        * **Soporte Oro:** El XAUUSD encuentra soporte fuerte en la zona de la EMA50.
        """)

else:
    st.error("⚠️ Error obteniendo datos de Yahoo Finance. Reintenta en 1 minuto.")

st.divider()
if st.button("🔄 ACTUALIZAR TODO"): st.rerun()
