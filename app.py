import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Gold Master Pro V6", layout="wide", initial_sidebar_state="collapsed")

# 2. CONEXIÓN A GOOGLE SHEETS (BASE DE DATOS)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Error de conexión a la base de datos. Verifica tus Secrets.")

def cargar_historial():
    try:
        # Cargamos los datos sin caché para ver actualizaciones inmediatas
        df = conn.read(ttl=0)
        return df.dropna(how="all")
    except:
        # Si la hoja está vacía, creamos la estructura básica
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
        st.toast(f"✅ Señal de {tipo} guardada en Google Sheets")
    except Exception as e:
        st.error(f"No se pudo guardar: {e}")

# 3. OBTENCIÓN DE DATOS DEL MERCADO
@st.cache_data(ttl=60)
def obtener_datos():
    try:
        gold = yf.Ticker("GC=F")
        # Pedimos suficientes datos para que las EMAs se calculen bien
        df = gold.history(period="2d", interval="5m")
        noticias = gold.news
        return df, noticias
    except:
        return pd.DataFrame(), []

# --- INICIO DE LA LÓGICA ---
df_raw, noticias = obtener_datos()

if not df_raw.empty:
    # 4. CÁLCULOS TÉCNICOS COMPLETOS
    df = df_raw.copy()
    df['ema20'] = ta.ema(df['Close'], length=20)
    df['ema50'] = ta.ema(df['Close'], length=50)
    df['rsi'] = ta.rsi(df['Close'], length=14)
    
    # Lógica de Velas Envolventes (Price Action)
    df['bull_eng'] = (df['Close'] > df['Open']) & (df['Close'].shift(1) < df['Open'].shift(1)) & (df['Close'] > df['Open'].shift(1))
    df['bear_eng'] = (df['Close'] < df['Open']) & (df['Close'].shift(1) > df['Open'].shift(1)) & (df['Close'] < df['Open'].shift(1))
    
    # Valores de la última vela cerrada
    last = df.iloc[-1]
    precio_actual = float(last['Close'])
    
    # Definición de Señales
    es_compra = (last['ema20'] > last['ema50']) and last['bull_eng'] and (last['rsi'] < 65)
    es_venta = (last['ema20'] < last['ema50']) and last['bear_eng'] and (last['rsi'] > 35)

    # 5. DISEÑO DE LA INTERFAZ
    col_main, col_news = st.columns([2, 1])

    with col_main:
        st.title("🔱 Gold Master Pro V6")
        
        # Panel de Señales
        if es_compra:
            st.success(f"### 🚀 SEÑAL DE COMPRA: {precio_actual:.2f}")
            if st.button("📥 REGISTRAR COMPRA EN EXCEL"):
                guardar_senal("COMPRA 🟢", precio_actual)
        elif es_venta:
            st.error(f"### 🔥 SEÑAL DE VENTA: {precio_actual:.2f}")
            if st.button("📥 REGISTRAR VENTA EN EXCEL"):
                guardar_senal("VENTA 🔴", precio_actual)
        else:
            st.info(f"🔎 Monitorizando... | Precio Actual: **{precio_actual:.2f}** | RSI: {last['rsi']:.1f}")

        # 6. CALCULADORA DE RIESGO AJUSTABLE
        st.divider()
        st.subheader("🧮 Gestión de Riesgo Personalizada")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            balance = st.number_input("Balance Cuenta ($)", value=1000.0, step=100.0)
            riesgo_pct = st.slider("Riesgo %", 0.5, 5.0, 1.0)
        
        with c2:
            puntos_sl = st.number_input("Puntos Stop Loss (SL)", value=3.0, step=0.5)
            puntos_tp = st.number_input("Puntos Take Profit (TP)", value=4.5, step=0.5)
            
        with c3:
            precio_entrada = st.number_input("Precio de Entrada", value=precio_actual)

        # Cálculo dinámico de niveles monetarios
        # Determinamos si es Short o Long para la calculadora
        es_short = es_venta or (precio_entrada < last['ema20'])
        sl_precio = precio_entrada + puntos_sl if es_short else precio_entrada - puntos_sl
        tp_precio = precio_entrada - puntos_tp if es_short else precio_entrada + puntos_tp
        
        dinero_riesgo = balance * (riesgo_pct / 100)
        ratio = puntos_tp / puntos_sl
        ganancia_posible = dinero_riesgo * ratio

        # Mostrar métricas de riesgo
        m1, m2, m3 = st.columns(3)
        m1.metric("🛡️ SL Precio", f"{sl_precio:.2f}")
        m2.metric("🎯 TP Precio", f"{tp_precio:.2f}")
        m3.metric("💰 Arriesgas", f"${dinero_riesgo:.2f}")
        
        st.write(f"**Proyección:** Si ganas, sumas **+${ganancia_posible:.2f}** (Ratio 1:{ratio:.1f})")

        # 7. HISTORIAL DE GOOGLE SHEETS
        st.divider()
        st.subheader("📜 Registro Histórico (Cloud)")
        historial_df = cargar_historial()
        if not historial_df.empty:
            st.dataframe(historial_df.iloc[::-1], use_container_width=True)
        else:
            st.write("La base de datos en la nube está esperando la primera señal.")

    with col_news:
        st.subheader("📰 Noticias Fundamentales")
        if noticias:
            for n in noticias[:6]:
                st.markdown(f"**[{n.get('title', 'Noticia sin título')}]({n.get('link', '#')})**")
                st.caption(f"Fuente: {n.get('publisher', 'Desconocida')}")
                st.divider()
        else:
            st.write("No hay noticias disponibles en este momento.")

else:
    st.warning("⚠️ No se reciben datos del mercado. Verifica la conexión a Internet o el Ticker de Yahoo.")

# Botón de actualización global
if st.button("🔄 ACTUALIZAR TODO"):
    st.rerun()
