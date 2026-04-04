import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración
st.set_page_config(page_title="Serge Financial Strategy v3.18", layout="wide")
st.title("🧬 Dashboard de Libertad Financiera")

# 2. Sidebar
with st.sidebar:
    st.header("⚙️ Variables")
    cap_inicial = st.number_input("Capital Inicial ($)", value=135000, step=5000)
    ahorro_mensual = st.number_input("Aporte Mensual ($)", value=2000, step=100)
    rendimiento_anual = st.number_input("Rendimiento Mercado (%)", value=10.0, step=0.5) / 100
    
    st.header("🏠 Inmueble")
    precio_hoy = st.number_input("Precio Aparta Hoy ($)", value=200000, step=5000)
    inflacion_inmueble = st.number_input("Inflación Inmueble (%)", value=4.0, step=0.5) / 100
    
    st.header("🎯 Meta de Retiro")
    liquidez_deseada = st.number_input("Liquidez Extra Inicial ($)", value=500000, step=10000)
    
    st.header("💸 Fase de Desembolso (Inflada)")
    retiro_buffer_hoy = st.number_input("Gasto 2 años (valor hoy $)", value=60000, step=5000)
    inflacion_gastos = st.number_input("Inflación de Gastos (%)", value=3.0, step=0.5) / 100
    
    años_proyeccion = st.slider("Horizonte (Años)", 4, 60, 40)

# 3. Motor de Cálculo
meses = años_proyeccion * 12
datos = []
capital_actual = cap_inicial
precio_aparta = precio_hoy
meta_lograda = False
año_meta = None
mes_de_la_compra = -1
gasto_buffer_ajustado = retiro_buffer_hoy 
año_agotamiento = None

inyectado_anual = 0
interes_anual = 0
retiro_anual = 0

# --- FILA GÉNESIS (AÑO 0 - 2026) ---
datos.append({
    "Año": 2026,
    "Capital ($)": round(cap_inicial),
    "Precio Apt": f"{round(precio_hoy):,}",
    "Inyectado ($)": 0,
    "Intereses ($)": 0,
    "Retiro ($)": 0,
    "Gasto_Invisible_2Y": round(retiro_buffer_hoy),
    "Status": "Inicio 🚀"
})

# --- LOOP DE SIMULACIÓN ---
for mes in range(1, meses + 1):
    año_actual = 2026 + (mes // 12)
    
    # Inflaciones mensuales
    if not meta_lograda:
        precio_aparta *= (1 + (inflacion_inmueble / 12))
    gasto_buffer_ajustado *= (1 + (inflacion_gastos / 12))

    # Lógica de Compra (Meta)
    if not meta_lograda and capital_actual >= (precio_aparta + liquidez_deseada):
        meta_lograda = True
        año_meta = año_actual
        mes_de_la_compra = mes
        gasto_total_inicial = precio_aparta + gasto_buffer_ajustado
        capital_actual -= gasto_total_inicial
        retiro_anual += gasto_total_inicial
    
    # Fase Activa vs Retiro
    if not meta_lograda:
        capital_actual += ahorro_mensual
        inyectado_anual += ahorro_mensual
    else:
        meses_desde_compra = mes - mes_de_la_compra
        if meses_desde_compra > 0 and meses_desde_compra % 24 == 0:
            capital_actual -= gasto_buffer_ajustado
            retiro_anual += gasto_buffer_ajustado
    
    # Interés Compuesto
    rendimiento_mes = capital_actual * (rendimiento_anual / 12)
    capital_actual += rendimiento_mes
    interes_anual += rendimiento_mes

    # Detección de agotamiento
    if capital_actual <= 0 and año_agotamiento is None:
        año_agotamiento = año_actual

    # Registro Anual (Diciembre de cada año)
    if mes % 12 == 0:
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital_actual) if capital_actual > 0 else 0,
            "Precio Apt": "COMPRADO" if meta_lograda else f"{round(precio_aparta):,}",
            "Inyectado ($)": round(inyectado_anual),
            "Intereses ($)": round(interes_anual),
            "Retiro ($)": round(retiro_anual),
            "Gasto_Invisible_2Y": round(gasto_buffer_ajustado),
            "Status": "Retiro 🌴" if meta_lograda else "Activo 💼"
        })
        inyectado_anual = 0
        interes_anual = 0
        retiro_anual = 0

df = pd.DataFrame(datos)

# 4. Layout
col_table, col_chart = st.columns([1.2, 0.8])
with col_table:
    st.subheader(f"📑 Proyección a {años_proyeccion} Años")
    st.dataframe(df.drop(columns=['Gasto_Invisible_2Y']).style.format({
        "Año": "{:.0f}", "Capital ($)": "{:,.0f}", 
        "Inyectado ($)": "{:,.0f}", "Intereses ($)": "{:,.0f}", "Retiro ($)": "{:,.0f}"
    }), height=600, use_container_width=True)

with col_chart:
    st.subheader("📈 Capital vs Gasto (Largo Plazo)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital Total", line=dict(color='royalblue', width=3)))
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Gasto_Invisible_2Y'], name="Costo Buffer (2Y)", line=dict(color='orange', dash='dot')))
    fig.update_layout(height=500, margin=dict(l=0, r=0, t=20, b=0), template="plotly_dark", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

# 5. KPIs
st.markdown("---")
k1, k2, k3 = st.columns(3)
with k1: 
    cap_final = df['Capital ($)'].iloc[-1]
    st.metric(f"Capital Final ({2026 + años_proyeccion})", f"${cap_final:,.0f}")
with k2: 
    st.metric("Buffer 2 Años (Valor Hoy)", f"${retiro_buffer_hoy:,.0f}")
with k3: 
    if meta_lograda: st.success(f"🎯 Meta en {año_meta}")
    else: st.error("🎯 Meta No Alcanzada")

# Alertas
if meta_lograda:
    if año_agotamiento:
        st.warning(f"⚠️ **Alerta de Sistema:** El capital se agota en el año **{año_agotamiento}**. Ajusta rendimiento o gastos.")
    else:
        st.info(f"🚀 **Libertad Financiera Lograda:** Apartamento comprado y retiro iniciado en el año **{año_meta}**. El capital es suficiente para cubrir los {años_proyeccion} años proyectados de forma sostenible.")
