import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gold Master Pro V6 - Cloud DB", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
# Nota: Necesitas configurar el secreto 'connections.gsheets.url' en Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos_sheets():
    try:
        return conn.read(ttl=5) # Lee la hoja con 5 segundos de caché
    except:
        return pd.DataFrame(columns=["Fecha", "Hora", "Tipo", "Precio"])

def guardar_senal_sheets(tipo, precio):
    nueva_fila = pd.DataFrame([{
        "Fecha": datetime.now().strftime("%Y-%m-%d"),
        "Hora": datetime.now().strftime("%H:%M:%S"),
        "Tipo": tipo,
        "Precio": round(precio, 2)
    }])
    
    df_actual = cargar_datos_sheets()
    
    # Evitar duplicar señal en el mismo minuto
    if df_actual.empty or df_actual.iloc[-1]["Hora"][:-3] != nueva_fila.iloc[0]["Hora"][:-3]:
        df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
        conn.update(data=df_final)
        return True
    return False

# --- CÁLCULOS TÉCNICOS ---
@st.cache_data(ttl=60)
def obtener_mercado():
    gold = yf.Ticker("GC=F")
    return gold.history(period="1d", interval="5m"), gold.news[:5]

df, noticias = obtener_mercado()

if not df.empty:
    # (Lógica de EMA y RSI omitida por brevedad, se mantiene igual al anterior)
    df['ema20'] = ta.ema(df['Close'], length=20)
    df['ema50'] = ta.ema(df['Close'], length=50)
    df['rsi'] = ta.rsi(df['Close'], length=14)
    precio_actual = df.iloc[-1]['Close']
    
    # Detección de Señales
    es_compra = (df['ema20'].iloc[-1] > df['ema50'].iloc[-1]) and (df['Close'].iloc[-1] > df['Open'].iloc[-1])
    es_venta = (df['ema20'].iloc[-1] < df['ema50'].iloc[-1]) and (df['Close'].iloc[-1] < df['Open'].iloc[-1])

    # Guardar automáticamente
    if es_compra: guardar_senal_sheets("COMPRA 🟢", precio_actual)
    if es_venta: guardar_senal_sheets("VENTA 🔴", precio_actual)

    # --- INTERFAZ ---
    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        st.subheader("📡 Radar Gold Master Pro")
        if es_compra: st.success(f"SEÑAL ACTIVA: COMPRA @ {precio_actual:.2f}")
        elif es_venta: st.error(f"SEÑAL ACTIVA: VENTA @ {precio_actual:.2f}")
        else: st.info("Buscando señal...")

        # Muestra la tabla de Google Sheets
        st.divider()
        st.subheader("📊 Historial Global (Google Sheets)")
        historial = cargar_datos_sheets()
        st.dataframe(historial.sort_index(ascending=False), use_container_width=True)

    with col_der:
        st.subheader("📰 Noticias Fundamentales")
        for n in noticias:
            st.markdown(f"**[{n['title']}]({n['link']})**")
            st.divider()

if st.button("🔄 Actualizar App"):
    st.rerun()
