import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gold Master Pro V6 - Elite", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Error configurando conexión a Sheets: {e}")

def cargar_datos_sheets():
    try:
        df = conn.read(ttl="1m")
        return df.dropna(how="all")
    except:
        return pd.DataFrame(columns=["Fecha", "Hora", "Tipo", "Precio"])

def guardar_senal_sheets(tipo, precio):
    df_actual = cargar_datos_sheets()
    ahora = datetime.now()
    nueva_fila = pd.DataFrame([{
        "Fecha": ahora.strftime("%Y-%m-%d"),
        "Hora": ahora.strftime("%H:%M:%S"),
        "Tipo": tipo,
        "Precio": round(float(precio), 2)
    }])
    
    # Solo guarda si la última señal no fue en el mismo minuto (evitar spam)
    if df_actual.empty or df_actual.iloc[-1]["Hora"][:-3] != nueva_fila.iloc[0]["Hora"][:-3]:
        df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
        conn.update(data=df_final)
        return True
    return False

# --- OBTENCIÓN DE DATOS DEL MERCADO ---
@st.cache_data(ttl=60)
def obtener_mercado():
    try:
        gold = yf.Ticker("GC=F")
        df = gold.history(period="1d", interval="5m")
        noticias = gold.news
        return df, noticias
    except:
        return pd.DataFrame(), []

# --- LÓGICA PRINCIPAL ---
df, noticias = obtener_mercado()

if not df.empty:
    # Cálculos Técnicos
    df['ema20'] = ta.ema(df['Close'], length=20)
    df['ema50'] = ta.ema(df['Close'], length=50)
    df['rsi'] = ta.rsi(df['Close'], length=14)
    
    precio_actual = float(df['Close'].iloc[-1])
    ema20_last = df['ema20'].iloc[-1]
    ema50_last = df['ema50'].iloc[-1]
    rsi_last = df['rsi'].iloc[-1]

    # Velas Envolventes
    bull_eng = (df['Close'] > df['Open']) & (df['Close'].shift(1) < df['Open'].shift(1))
    bear_eng = (df['Close'] < df['Open']) & (df['Close'].shift(1) > df['Open'].shift(1))
    
    es_compra = (ema20_last > ema50_last) and bull_eng.iloc[-1] and (rsi_last < 65)
    es_venta = (ema20_last < ema50_last) and bear_eng.iloc[-1] and (rsi_last > 35)

    if es_compra: guardar_senal_sheets("COMPRA 🟢", precio_actual)
    if es_venta: guardar_senal_sheets("VENTA 🔴", precio_actual)

    # --- INTERFAZ ---
    col_main, col_news = st.columns([2, 1])

    with col_main:
        st.subheader("📡 Radar de Mercado")
        if es_compra: st.success(f"🚀 SEÑAL ACTIVA: COMPRA @ {precio_actual:.2f}")
        elif es_venta: st.error(f"🔥 SEÑAL ACTIVA: VENTA @ {precio_actual:.2f}")
        else: st.info(f"⏳ Buscando Oportunidades... | Precio: {precio_actual:.2f}")

        # --- CALCULADORA ---
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            puntos_sl = st.number_input("Puntos SL", value=3.0, step=0.5)
            puntos_tp = st.number_input("Puntos TP", value=4.5, step=0.5)
        with c2:
            balance = st.number_input("Balance ($)", value=1000.0)
            riesgo_pct = st.slider("Riesgo %", 0.1, 5.0, 1.0)

        # Cálculo de TP/SL dinámico
        es_short = es_venta or (precio_actual < ema20_last)
        sl = precio_actual + puntos_sl if es_short else precio_actual - puntos_sl
        tp = precio_actual - puntos_tp if es_short else precio_actual + puntos_tp
        
        st.write(f"**Sugerencia:** SL: {sl:.2f} | TP: {tp:.2f} | Riesgo: ${balance*(riesgo_pct/100):.2f}")

        # --- HISTORIAL ---
        st.divider()
        st.subheader("📊 Historial en Google Sheets")
        historial = cargar_datos_sheets()
        if not historial.empty:
            st.dataframe(historial.iloc[::-1], use_container_width=True)

    with col_news:
        st.subheader("📰 Noticias")
        if noticias:
            for n in noticias:
                # El .get() evita el KeyError si Yahoo no envía el título o link
                titulo = n.get('title', 'Sin título')
                link = n.get('link', '#')
                st.markdown(f"**[{titulo}]({link})**")
                st.divider()
        else:
            st.write("Cargando noticias...")

else:
    st.error("Esperando datos de Yahoo Finance...")

if st.button("🔄 Sincronizar"):
    st.rerun()
