import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración
YEAR_ACTUAL = datetime.now().year
st.set_page_config(page_title="Serge Rental Strategy v1.6", layout="wide")
st.title("🏢 Estrategia de Libertad Financiera (Alquiler)")

MESES_NOMBRES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# 2. Sidebar
with st.sidebar:
    st.header("⚙️ Fase de Acumulación")
    cap_inicial = st.number_input("Capital Inicial ($)", value=135000, step=5000)
    ahorro_mensual = st.number_input("Aporte Mensual ($)", value=2000, step=100)
    rendimiento_anual = st.number_input("Rendimiento Mercado (%)", value=10.0, step=0.5) / 100
    
    st.header("🏢 Fase de Independencia")
    renta_hoy = st.number_input(f"Alquiler Objetivo (valor {YEAR_ACTUAL}) ($)", value=1200, step=100)
    inflacion_renta = st.number_input("Inflación Alquiler (%)", value=3.5, step=0.5) / 100
    
    st.header("🎯 Objetivo de Capital")
    liquidez_deseada = st.number_input("Capital Mínimo Requerido ($)", value=500000, step=10000)
    
    st.header("💸 Costo de Vida Independiente")
    retiro_buffer_hoy = st.number_input(f"Gasto Bianual (SIN renta) (valor {YEAR_ACTUAL} $)", value=60000, step=5000)
    inflacion_gastos = st.number_input("Inflación de Gastos (%)", value=3.0, step=0.5) / 100
    
    años_proyeccion = st.slider("Horizonte de Proyección (Años)", 4, 60, 48)

    st.header("🛡️ Plan de Contingencia")
    años_extra_trabajo = st.slider("Años de Capitalización Extra (Post-Meta)", 0, 15, 0)
    inversion_extra_mensual = st.number_input("Inversión Extra Mensual ($)", value=0, step=100)

# 3. Motor de Cálculo
meses = años_proyeccion * 12
datos = []
capital_actual = cap_inicial
meta_lograda = False
año_meta = None ; mes_nombre_meta = "" ; mes_de_la_meta = -1
año_agotamiento = None
renta_proyectada = renta_hoy
gasto_buffer_proyectado = retiro_buffer_hoy
año_final_proy = YEAR_ACTUAL + años_proyeccion

total_pagado_renta = 0
renta_al_inicio_independencia = 0
inyectado_anual = 0 ; retiro_anual = 0

for mes in range(1, meses + 1):
    año_actual = YEAR_ACTUAL + (mes // 12)
    renta_proyectada *= (1 + (inflacion_renta / 12))
    gasto_buffer_proyectado *= (1 + (inflacion_gastos / 12))

    if not meta_lograda and capital_actual >= liquidez_deseada:
        meta_lograda = True
        año_meta = año_actual
        mes_nombre_meta = MESES_NOMBRES[mes % 12]
        mes_de_la_meta = mes

    if not meta_lograda:
        capital_actual += ahorro_mensual
        inyectado_anual += ahorro_mensual
    else:
        meses_desde_meta = mes - mes_de_la_meta
        periodo_gracia_meses = (años_extra_trabajo * 12)
        
        if meses_desde_meta <= periodo_gracia_meses:
            capital_actual += inversion_extra_mensual
            inyectado_anual += inversion_extra_mensual
        else:
            if renta_al_inicio_independencia == 0:
                renta_al_inicio_independencia = renta_proyectada
            
            capital_actual -= renta_proyectada
            total_pagado_renta += renta_proyectada
            retiro_anual += renta_proyectada
            
            meses_independencia = meses_desde_meta - periodo_gracia_meses
            if meses_independencia == 1 or (meses_independencia > 1 and meses_independencia % 24 == 0):
                capital_actual -= gasto_buffer_proyectado
                retiro_anual += gasto_buffer_proyectado
    
    capital_actual += capital_actual * (rendimiento_anual / 12)
    if capital_actual <= 0 and año_agotamiento is None: año_agotamiento = año_actual

    if mes % 12 == 0:
        es_independiente = meta_lograda and (mes - mes_de_la_meta > (años_extra_trabajo * 12))
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital_actual) if capital_actual > 0 else 0,
            "Renta Mens.": round(renta_proyectada) if es_independiente else 0,
            "Total Renta Acum.": round(total_pagado_renta),
            "Inyectado ($)": round(inyectado_anual),
            "Retiro ($)": round(retiro_anual),
            "Status": "Independiente 🌴" if es_independiente else "Acumulación 💼"
        })
        inyectado_anual = 0 ; retiro_anual = 0

df = pd.DataFrame(datos)

# 4. Layout
col_table, col_chart = st.columns([1.1, 0.9])
with col_table:
    st.subheader("📑 Simulación de Independencia Financiera")
    st.dataframe(df.drop(columns=['Total Renta Acum.']).style.format({
        "Año": "{:.0f}", "Capital ($)": "{:,.0f}", 
        "Inyectado ($)": "{:,.0f}", "Retiro ($)": "{:,.0f}"
    }), height=400, use_container_width=True, hide_index=True)

with col_chart:
    st.subheader("📈 Capital vs Gasto Proyectado")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='#00d1b2', width=3)))
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Total Renta Acum.'], name="Renta Acumulada", line=dict(color='#ff4b4b')))
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=20,b=0), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

# 5. KPIs
st.markdown("---")
k1, k2, k3 = st.columns(3)
k1.metric(f"Capital Final ({año_final_proy})", f"${capital_actual:,.0f}")
k2.metric(f"Monto del Buffer (Hoy {YEAR_ACTUAL})", f"${retiro_buffer_hoy:,.0f}")
k3.metric("Gasto Total en Renta", f"${total_pagado_renta:,.0f}")

if meta_lograda:
    usa_plan = años_extra_trabajo > 0
    año_independencia = año_meta + (años_extra_trabajo if usa_plan else 0)
    if año_agotamiento:
        st.warning(f"⚠️ **Atención:** Libertad alcanzada en {año_independencia}, pero el capital se agota en {año_agotamiento}.")
    else:
        info_txt = f"Objetivo alcanzado en {mes_nombre_meta} de {año_meta}"
        if usa_plan: info_txt += f" con inicio de independencia financiera en **{año_independencia}**."
        else: info_txt += " con independencia financiera inmediata."
        st.info(f"🚀\n\n**Libertad Financiera Lograda:** {info_txt} El capital es suficiente hasta el año **{año_final_proy}** de forma sostenible.")

st.markdown("---")
m1, m2 = st.columns(2)
m1.markdown(f"<p style='font-size:16px; margin-bottom:0px;'>🟢 Costo Renta al Inicio ({año_independencia if meta_lograda else '?'})</p><p style='font-size:24px; color:#28a745; font-weight:bold; margin-top:0px;'>${renta_al_inicio_independencia:,.0f}/mes</p>", unsafe_allow_html=True)
m2.markdown(f"<p style='font-size:16px; margin-bottom:0px;'>🔴 Costo Renta Final Proyectado ({año_final_proy})</p><p style='font-size:24px; color:#ff4b4b; font-weight:bold; margin-top:0px;'>${renta_proyectada:,.0f}/mes</p>", unsafe_allow_html=True)
