import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración
YEAR_ACTUAL = datetime.now().year
st.set_page_config(page_title="Serge Rental Strategy v1.2", layout="wide")
st.title("🏢 Dashboard de Libertad Financiera (Alquiler)")

MESES_NOMBRES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# 2. Sidebar
with st.sidebar:
    st.header("⚙️ Variables")
    cap_inicial = st.number_input("Capital Inicial ($)", value=135000, step=5000)
    ahorro_mensual = st.number_input("Aporte Mensual ($)", value=2000, step=100)
    rendimiento_anual = st.number_input("Rendimiento Mercado (%)", value=10.0, step=0.5) / 100
    
    st.header("🏢 Alquiler")
    renta_hoy = st.number_input(f"Alquiler Mensual (valor {YEAR_ACTUAL}) ($)", value=1200, step=100)
    inflacion_renta = st.number_input("Inflación Alquiler (%)", value=3.5, step=0.5) / 100
    
    st.header("🎯 Meta de Retiro")
    liquidez_deseada = st.number_input("Capital mínimo para retiro ($)", value=500000, step=10000)
    
    st.header("💸 Gastos de Vida")
    retiro_buffer_hoy = st.number_input(f"Gasto bianual SIN renta (valor {YEAR_ACTUAL} $)", value=60000, step=5000)
    inflacion_gastos = st.number_input("Inflación de Gastos (%)", value=3.0, step=0.5) / 100
    
    años_proyeccion = st.slider("Horizonte de proyección (Años)", 4, 60, 48)

    st.header("🛡️ Plan de Contingencia")
    años_extra_trabajo = st.slider("Años extra de trabajo post-meta", 0, 15, 0)
    inversion_extra_mensual = st.number_input("Inversión mensual extra ($)", value=0, step=100)

# 3. Motor de Cálculo
meses = años_proyeccion * 12
datos = []
capital_actual = cap_inicial
meta_lograda = False
año_meta = None ; mes_nombre_meta = "" ; mes_de_la_meta = -1
año_agotamiento = None
renta_actualizada = renta_hoy
gasto_buffer_ajustado = retiro_buffer_hoy
año_final_proy = YEAR_ACTUAL + años_proyeccion

# Contadores para KPIs
total_pagado_renta = 0
renta_al_inicio_retiro = 0
renta_al_final = 0

inyectado_anual = 0 ; retiro_anual = 0

for mes in range(1, meses + 1):
    año_actual = YEAR_ACTUAL + (mes // 12)
    
    renta_actualizada *= (1 + (inflacion_renta / 12))
    gasto_buffer_ajustado *= (1 + (inflacion_gastos / 12))

    if not meta_lograda and capital_actual >= liquidez_deseada:
        meta_lograda = True
        año_meta = año_actual
        mes_nombre_meta = MESES_NOMBRES[mes % 12]
        mes_de_la_meta = mes
        renta_al_inicio_retiro = renta_actualizada

    if not meta_lograda:
        capital_actual += ahorro_mensual
        inyectado_anual += ahorro_mensual
    else:
        meses_desde_meta = mes - mes_de_la_meta
        usa_plan = años_extra_trabajo > 0
        periodo_gracia_meses = (años_extra_trabajo * 12) if usa_plan else 0
        es_periodo_extra = meses_desde_meta <= periodo_gracia_meses
        
        if es_periodo_extra:
            capital_actual += inversion_extra_mensual
            inyectado_anual += inversion_extra_mensual
        else:
            # Fase de Retiro Real
            capital_actual -= renta_actualizada
            total_pagado_renta += renta_actualizada
            retiro_anual += renta_actualizada
            
            meses_post_trabajo = meses_desde_meta - periodo_gracia_meses
            if meses_post_trabajo == 1 or (meses_post_trabajo > 1 and meses_post_trabajo % 24 == 0):
                capital_actual -= gasto_buffer_ajustado
                retiro_anual += gasto_buffer_ajustado
    
    capital_actual += capital_actual * (rendimiento_anual / 12)
    if capital_actual <= 0 and año_agotamiento is None: año_agotamiento = año_actual

    if mes % 12 == 0:
        renta_al_final = renta_actualizada
        es_retiro = meta_lograda and (mes - mes_de_la_meta > (años_extra_trabajo * 12))
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital_actual) if capital_actual > 0 else 0,
            "Renta Mens.": round(renta_actualizada),
            "Inyectado ($)": round(inyectado_anual),
            "Retiro ($)": round(retiro_anual),
            "Status": "Retiro 🌴" if es_retiro else "Activo 💼"
        })
        inyectado_anual = 0 ; retiro_anual = 0

df = pd.DataFrame(datos)

# 4. Visualización - KPIs Superiores
st.markdown("---")
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(f"Capital Final ({año_final_proy})", f"${capital_actual:,.0f}")
kpi2.metric(f"Buffer 2 años (Ajustado)", f"${gasto_buffer_ajustado:,.0f}")
kpi3.metric("Total Renta Pagada (Vida)", f"${total_pagado_renta:,.0f}")

st.markdown("---")
kpi4, kpi5 = st.columns(2)
kpi4.write(f"🏷️ **Renta al iniciar retiro:** ${renta_al_inicio_retiro:,.0f}/mes")
kpi5.write(f"📈 **Renta al final ({año_final_proy}):** ${renta_al_final:,.0f}/mes")

# Gráficos y Tabla
col_table, col_chart = st.columns([1.2, 0.8])
with col_table:
    st.subheader("📑 Simulación Detallada")
    st.dataframe(df.style.format({
        "Año": "{:.0f}", "Capital ($)": "{:,.0f}", 
        "Inyectado ($)": "{:,.0f}", "Retiro ($)": "{:,.0f}"
    }), height=400, use_container_width=True, hide_index=True)

with col_chart:
    st.subheader("📈 Curva de Capital")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='#00d1b2', width=3)))
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig, use_container_width=True)

# Banners de Análisis
if meta_lograda:
    usa_plan = años_extra_trabajo > 0
    año_libertad = año_meta + (años_extra_trabajo if usa_plan else 0)
    if año_agotamiento:
        st.warning(f"⚠️ **Alerta:** Meta alcanzada en {mes_nombre_meta} {año_meta}, pero el capital se agota en **{año_agotamiento}**.")
    else:
        st.success(f"🚀 **Libertad Lograda:** Retiro sostenible hasta **{año_final_proy}**. Inicio: {año_libertad}.")
