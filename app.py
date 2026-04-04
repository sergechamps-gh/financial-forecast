import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración
st.set_page_config(page_title="Serge Financial Strategy v3.7", layout="wide")
st.title("🛡️ Dashboard de Libertad Financiera: Real Cash-Out Edition")

# 2. Sidebar
with st.sidebar:
    st.header("⚙️ Variables")
    cap_inicial = st.number_input("Capital Inicial ($)", value=135000, step=5000)
    ahorro_mensual = st.number_input("Aporte Mensual ($)", value=2000, step=100)
    rendimiento_anual = st.number_input("Rendimiento Mercado (%)", value=10, step=1) / 100
    
    st.header("🏠 Inmueble")
    precio_hoy = st.number_input("Precio Aparta Hoy ($)", value=200000, step=5000)
    inflacion_inmueble = st.number_input("Inflación Inmueble (%)", value=4, step=1) / 100
    
    st.header("🎯 Meta de Retiro")
    liquidez_deseada = st.number_input("Liquidez Extra Inicial ($)", value=500000, step=10000)
    
    st.header("💸 Fase de Desembolso")
    retiro_buffer = st.number_input("Retiro cada 2 años ($)", value=60000, step=5000)
    
    años_proyeccion = st.slider("Horizonte (Años)", 4, 40, 20)

# 3. Motor de Cálculo Realista
meses = años_proyeccion * 12
datos = []
capital = cap_inicial
precio_aparta = precio_hoy
intereses_acumulados = 0
meta_lograda = False
año_meta = None
mes_de_la_compra = -1

# Acumuladores anuales para la tabla
inyectado_anual = 0
interes_anual = 0
retiro_anual = 0

for mes in range(meses + 1):
    año_actual = 2026 + (mes // 12)
    
    # Inflación Inmueble (Solo hasta que se compra)
    if not meta_lograda and mes > 0:
        precio_aparta = precio_aparta * (1 + (inflacion_inmueble / 12))

    # --- EVENTO DE COMPRA Y RETIRO INICIAL ---
    if not meta_lograda and capital >= (precio_aparta + liquidez_deseada):
        meta_lograda = True
        año_meta = año_actual
        mes_de_la_compra = mes
        
        # RESTA REAL DEL CAPITAL
        gasto_compra = precio_aparta + retiro_buffer
        capital -= gasto_compra
        retiro_anual += gasto_compra
    
    # --- LÓGICA DE APORTES VS RETIROS POST-COMPRA ---
    if not meta_lograda:
        if mes > 0:
            aporte = ahorro_mensual
            capital += aporte
            inyectado_anual += aporte
    else:
        # Si ya compró, check de retiro cada 2 años (24 meses)
        meses_desde_compra = mes - mes_de_la_compra
        if meses_desde_compra > 0 and meses_desde_compra % 24 == 0:
            capital -= retiro_buffer
            retiro_anual += retiro_buffer
    
    # --- RENDIMIENTO DEL MERCADO (Sobre el capital remanente) ---
    rendimiento_mes = capital * (rendimiento_anual / 12)
    capital += rendimiento_mes
    interes_anual += rendimiento_mes
    intereses_acumulados += rendimiento_mes

    # --- REGISTRO ANUAL ---
    if mes % 12 == 0 and mes > 0:
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital),
            "Precio Apt": "COMPRADO" if meta_lograda else f"{round(precio_aparta):,}",
            "Inyectado ($)": round(inyectado_anual),
            "Intereses ($)": round(interes_anual),
            "Retiro ($)": round(retiro_anual),
            "Status": "Retiro 🌴" if meta_lograda else "Activo 💼"
        })
        # Reset de acumuladores anuales
        inyectado_anual = 0
        interes_anual = 0
        retiro_anual = 0

df = pd.DataFrame(datos)

# 4. Layout
col_table, col_chart = st.columns([1.2, 0.8])

with col_table:
    st.subheader("📑 Raw Numbers (Corte Anual)")
    st.dataframe(
        df.style.format({
            "Año": "{:.0f}", "Capital ($)": "{:,.0f}", 
            "Inyectado ($)": "{:,.0f}", "Intereses ($)": "{:,.0f}", "Retiro ($)": "{:,.0f}"
        }), 
        height=550, use_container_width=True
    )

with col_chart:
    st.subheader("📈 Proyección Visual Real")
    fig = go.Figure()
    # Línea de Capital (Verás la caída en el año de meta)
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital Remanente", line=dict(color='royalblue', width=3)))
    
    # Precio Apt (Solo hasta la meta)
    df_apt = df[df['Precio Apt'] != "COMPRADO"]
    if not df_apt.empty:
        precios_v = [float(str(x).replace(',', '')) for x in df_apt['Precio Apt']]
        fig.add_trace(go.Scatter(x=df_apt['Año'], y=precios_v, name="Precio Apt", line=dict(color='firebrick', dash='dot')))
    
    fig.update_layout(height=450, margin=dict(l=0, r=0, t=20, b=0), hovermode="x unified", template="plotly_dark", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

# 5. KPIs
st.markdown("---")
k1, k2, k3 = st.columns(3)
with k1: st.metric("Rendimiento Total", f"${intereses_acumulados:,.0f}")
with k2: st.metric("Costo Buffer (Vida)", f"${retiro_buffer:,.0f} / 2 años")
with k3: 
    if meta_lograda: st.success(f"🎯 Comprado & Libre en {año_meta}")
    else: st.error("🎯 Meta no alcanzada")

if meta_lograda:
    st.info(f"💡 **Análisis:** En el año {año_meta} sacaste capital para pagar la casa y fondear tus primeros 2 años. El capital restante sigue trabajando para ti.")
