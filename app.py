import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. Configuración limpia
st.set_page_config(page_title="Gold Master Pro V6", layout="wide")

# 2. Conexión a Base de Datos con manejo de errores
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.sidebar.error("Error de configuración en Sheets. Revisa los Secrets.")

def cargar_historial():
    try:
        # ttl=0 para ver los cambios de inmediato al actualizar
        return conn.read(ttl=0).dropna(how="all")
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
        return True
    except:
        return False

# 3. Obtención de Datos
@st.cache_data(ttl=60)
def obtener_datos():
    try:
        gold = yf.Ticker("GC=F")
        df = gold.history(period="1d", interval="5m")
        noticias = gold.news
        return df, noticias
    except:
        return pd.DataFrame(), []

# --- EJECUCIÓN ---
df, noticias = obtener_datos()

if not df.empty:
    # Cálculos rápidos
    df['ema20'] = ta.ema(df['Close'], length=20)
    df['ema50'] = ta.ema(df['Close'], length=50)
    df['rsi'] = ta.rsi(df['Close'], length=14)
    
    # Datos de la última vela
    p_actual = float(df['Close'].iloc[-1])
    e20 = df['ema20'].iloc[-1]
    e50 = df['ema50'].iloc[-1]
    r = df['rsi'].iloc[-1]
    
    # Lógica de Señal (Simplificada para estabilidad)
    es_compra = (e20 > e50) and (p_actual > e20) and (r < 65)
    es_venta = (e20 < e50) and (p_actual < e20) and (r > 35)

    # Interfaz en dos columnas
    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        st.header("🔱 Radar de Oro")
        if es_compra:
            st.success(f"🚀 SEÑAL: COMPRA @ {p_actual:.2f}")
            if st.button("📝 Registrar Compra en Excel"):
                guardar_senal("COMPRA 🟢", p_actual)
                st.toast("¡Guardado en Google Sheets!")
        elif es_venta:
            st.error(f"🔥 SEÑAL: VENTA @ {p_actual:.2f}")
            if st.button("📝 Registrar Venta en Excel"):
                guardar_senal("VENTA 🔴", p_actual)
                st.toast("¡Guardado en Google Sheets!")
        else:
            st.info(f"⏳ Buscando... Precio actual: {p_actual:.2f}")

        st.divider()
        st.subheader("📊 Historial de la Nube")
        st.dataframe(cargar_historial().iloc[::-1], use_container_width=True)

    with col_der:
        st.header("📰 Noticias")
        if noticias:
            for n in noticias[:5]:
                st.markdown(f"**[{n.get('title', 'Sin título')}]({n.get('link', '#')})**")
                st.divider()

else:
    st.warning("Conectando con el mercado... por favor espera.")

if st.button("🔄 Actualizar Todo"):
    st.rerun()
