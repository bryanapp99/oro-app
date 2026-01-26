# ... (mantén los imports y la configuración de arriba)

# --- 1. OBTENER DATOS (v11) ---
data = yf.download("GC=F", interval=intervalo, period="7d")

if not data.empty and len(data) > 20:
    df = data.copy()
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # Indicadores
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    current_price = float(df['Close'].iloc[-1])
    current_rsi = float(df['RSI'].iloc[-1])
    current_ema = float(df['EMA_20'].iloc[-1])

    # --- LÓGICA DE SEÑAL ---
    signal = "ESPERAR"
    if current_price > current_ema and current_rsi < 45: signal = "COMPRA"
    elif current_price < current_ema and current_rsi > 55: signal = "VENTA"

    # --- INTERFAZ PRINCIPAL ---
    st.markdown(f"<h1 style='text-align: center; color: #FFD700;'>🥇 XAU/USD TERMINAL</h1>", unsafe_allow_html=True)
    
    # CUADRO DE SEÑAL Y SIMULADOR (JUNTOS)
    col_izq, col_der = st.columns([1, 1])

    with col_izq:
        st.subheader("📢 Señal Actual")
        color = "#28a745" if signal == "COMPRA" else "#dc3545" if signal == "VENTA" else "#6c757d"
        st.markdown(f"<div style='background:{color};padding:20px;border-radius:10px;text-align:center;color:white'><h1>{signal}</h1><p>Precio: ${current_price:,.2f}</p></div>", unsafe_allow_html=True)

    with col_der:
        st.subheader("🧮 Gestión de Riesgo")
        cap = st.number_input("Capital ($)", value=1000.0, step=100.0)
        riesgo = st.slider("% Riesgo", 0.5, 5.0, 1.0)
        st.write(f"Arriesgas: **${(cap * (riesgo/100)):.2f}**")
        if signal != "ESPERAR":
            # TP de 50 pips y SL de 30 pips para el Oro
            tp_sug = current_price + 5.0 if signal == "COMPRA" else current_price - 5.0
            sl_sug = current_price - 3.0 if signal == "COMPRA" else current_price + 3.0
            st.success(f"🎯 TP: {tp_sug:.2f} | 🛑 SL: {sl_sug:.2f}")

    # --- GRÁFICO ---
    st.write("---")
    # ... (aquí sigue el código del gráfico de velas que ya tienes)
