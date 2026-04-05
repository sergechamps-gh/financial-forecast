import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración
st.set_page_config(page_title="Serge Financial Strategy v3.33", layout="wide")
st.title("🧬 Dashboard de Libertad Financiera")

# Lista de meses para el reporte
MESES_NOMBRES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

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
    
    st.header("💸 Fase de Desembolso")
    retiro_buffer_hoy = st.number_input("Gasto 2 años (valor hoy $)", value=60000, step=5000)
    inflacion_gastos = st.number_input("Inflación de Gastos (%)", value=3.0, step=0.5) / 100
    
    años_proyeccion = st.slider("Horizonte (Años)", 4, 60, 48)

    st.header("🛡️ Plan de Contingencia")
    años_extra_trabajo = st.slider("Años extra de trabajo post-compra", 0, 10, 0)
    inversion_extra_mensual = st.number_input("Inversión mensual extra ($)", value=0, step=100)

# 3. Motor de Cálculo
meses = años_proyeccion * 12
datos = []
capital_actual = cap_inicial
precio_aparta = precio_hoy
meta_lograda = False
año_meta = None
mes_nombre_meta = ""
mes_de_la_compra = -1
gasto_buffer_ajustado = retiro_buffer_hoy 
año_agotamiento = None
costo_final_aparta = 0
capital_post_meta = 0

inyectado_anual = 0
interes_anual = 0
retiro_anual = 0

# Fila Génesis
datos.append({
    "Año": 2026, "Capital ($)": round(cap_inicial), "Precio Apt": f"{round(precio_hoy):,}",
    "Inyectado ($)": 0, "Intereses ($)": 0, "Retiro ($)": 0, 
    "Gasto_2Y": round(retiro_buffer_hoy), "Status": "Inicio 🚀"
})

for mes in range(1, meses + 1):
    año_actual = 2026 + (mes // 12)
    # Calculamos el nombre del mes basado en el índice (0-11)
    nombre_mes_actual = MESES_NOMBRES[mes % 12]
    
    if not meta_lograda:
        precio_aparta *= (1 + (inflacion_inmueble / 12))
    gasto_buffer_ajustado *= (1 + (inflacion_gastos / 12))

    # HITO DE COMPRA
    if not meta_lograda and capital_actual >= (precio_aparta + liquidez_deseada):
        meta_lograda = True
        año_meta = año_actual
        mes_nombre_meta = nombre_mes_actual
        mes_de_la_compra = mes
        costo_final_aparta = precio_aparta
        
        usa_plan = años_extra_trabajo > 0 and inversion_extra_mensual > 0
        gasto_inicial = precio_aparta + (gasto_buffer_ajustado if not usa_plan else 0)
        
        capital_actual -= gasto_inicial
        capital_post_meta = capital_actual
        retiro_anual += gasto_inicial
    
    if not meta_lograda:
        capital_actual += ahorro_mensual
        inyectado_anual += ahorro_mensual
    else:
        meses_desde_compra = mes - mes_de_la_compra
        usa_plan = años_extra_trabajo > 0 and inversion_extra_mensual > 0
        es_periodo_extra = usa_plan and meses_desde_compra <= (años_extra_trabajo * 12)
        
        if es_periodo_extra:
            capital_actual += inversion_extra_mensual
            inyectado_anual += inversion_extra_mensual
        else:
            periodo_gracia = (años_extra_trabajo * 12) if usa_plan else 0
            meses_post_trabajo = meses_desde_compra - periodo_gracia
            
            if meses_post_trabajo == 1 or (meses_post_trabajo > 1 and meses_post_trabajo % 24 == 0):
                capital_actual -= gasto_buffer_ajustado
                retiro_anual += gasto_buffer_ajustado
    
    rendimiento_mes = capital_actual * (rendimiento_anual / 12)
    capital_actual += rendimiento_mes
    interes_anual += rendimiento_mes

    if capital_actual <= 0 and año_agotamiento is None:
        año_agotamiento = año_actual

    if mes % 12 == 0:
        periodo_gracia = (años_extra_trabajo * 12) if (años_extra_trabajo > 0 and inversion_extra_mensual > 0) else 0
        es_retiro = meta_lograda and (mes - mes_de_la_compra > periodo_gracia)
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital_actual) if capital_actual > 0 else 0,
            "Precio Apt": "COMPRADO" if meta_lograda else f"{round(precio_aparta):,}",
            "Inyectado ($)": round(inyectado_anual),
            "Intereses ($)": round(interes_anual),
            "Retiro ($)": round(retiro_anual),
            "Gasto_2Y": round(gasto_buffer_ajustado),
            "Status": "Retiro 🌴" if es_retiro else "Activo 💼"
        })
        inyectado_anual = 0; interes_anual = 0; retiro_anual = 0

df = pd.DataFrame(datos)

# 4. Layout
col_table, col_chart = st.columns([1.2, 0.8])
with col_table:
    st.subheader(f"📑 Proyección a {años_proyeccion} Años")
    st.dataframe(df.drop(columns=['Gasto_2Y']).style.format({
        "Año": "{:.0f}", "Capital ($)": "{:,.0f}", 
        "Inyectado ($)": "{:,.0f}", "Intereses ($)": "{:,.0f}", "Retiro ($)": "{:,.0f}"
    }), height=400, use_container_width=True)

with col_chart:
    st.subheader("📈 Capital vs Gasto")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='royalblue', width=3)))
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Gasto_2Y'], name="Gasto (2Y)", line=dict(color='orange', dash='dot')))
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=20, b=0), template="plotly_dark", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

# 5. KPIs y Banners
st.markdown("---")
k1, k2, k3 = st.columns(3)
with k1: st.metric(f"Capital Final ({2026 + años_proyeccion})", f"${df['Capital ($)'].iloc[-1]:,}")
with k2: st.metric("Buffer 2 Años (Hoy)", f"${retiro_buffer_hoy:,}")
with k3: 
    if meta_lograda: 
        # KPI VERDE ACTUALIZADO CON MES
        st.success(f"🎯 Compra de apartamento en {mes_nombre_meta} {año_meta}")
    else: 
        st.error("🎯 Meta No Alcanzada")

if meta_lograda:
    usa_plan = años_extra_trabajo > 0 and inversion_extra_mensual > 0
    año_libertad = año_meta + (años_extra_trabajo if usa_plan else 0)
    
    if año_agotamiento:
        st.warning(f"⚠️\n\n**Alerta de Sistema:** El capital se agota en el año **{año_agotamiento}**. Ajusta rendimiento, gastos o aplica el plan de contingencia.")
    else:
        inicio_texto = f"Apartamento comprado en {mes_nombre_meta} de {año_meta}"
        if usa_plan:
            # Si hay plan de contingencia, el retiro empieza el mismo mes pero años después
            inicio_texto += f" y retiro iniciado en {mes_nombre_meta} de **{año_libertad}**"
        else:
            inicio_texto += " y retiro iniciado inmediatamente"
            
        st.info(f"🚀\n\n**Libertad Financiera Lograda:** {inicio_texto}. El capital es suficiente para cubrir los {años_proyeccion} años proyectados de forma sostenible.")

    st.markdown("---")
    m1, m2 = st.columns(2)
    m1.write(f"🏠 **Costo Final Apartamento:** `${costo_final_aparta:,.0f}`")
    m2.write(f"💰 **Capital Post-Compra:** `${capital_post_meta:,.0f}`")
