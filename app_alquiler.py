import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración
YEAR_ACTUAL = datetime.now().year
st.set_page_config(page_title="Serge Independence Strategy v1.5", layout="wide")
st.title("🏠 Estrategia de Independencia: Salida de Casa (Alquiler)")

MESES_NOMBRES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# 2. Sidebar
with st.sidebar:
    st.header("⚙️ Fase Actual (Con Padres)")
    cap_inicial = st.number_input("Capital Inicial ($)", value=135000, step=5000)
    ahorro_mensual = st.number_input("Ahorro Mensual Actual ($)", value=2000, step=100)
    rendimiento_anual = st.number_input("Rendimiento Mercado (%)", value=10.0, step=0.5) / 100
    
    st.header("🏢 Fase Independiente (Alquiler)")
    renta_hoy = st.number_input(f"Alquiler deseado (valor {YEAR_ACTUAL}) ($)", value=1200, step=100)
    inflacion_renta = st.number_input("Inflación Alquiler (%)", value=3.5, step=0.5) / 100
    
    st.header("🎯 Meta de Salida")
    liquidez_deseada = st.number_input("Capital mínimo para salir ($)", value=500000, step=10000)
    
    st.header("💸 Gastos de Vida Solo")
    retiro_buffer_hoy = st.number_input(f"Gasto bianual SIN renta (valor {YEAR_ACTUAL} $)", value=60000, step=5000)
    inflacion_gastos = st.number_input("Inflación de Gastos (%)", value=3.0, step=0.5) / 100
    
    años_proyeccion = st.slider("Horizonte total (Años)", 4, 60, 48)

    st.header("🛡️ Plan de Contingencia")
    años_extra_trabajo = st.slider("Años extra viviendo con padres post-meta", 0, 15, 0)
    inversion_extra_mensual = st.number_input("Inversión mensual extra ($)", value=0, step=100)

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
    # La inflación siempre corre, aunque no estemos pagando aún
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
        
        # ¿Sigue con sus padres trabajando extra?
        if meses_desde_meta <= periodo_gracia_meses:
            capital_actual += inversion_extra_mensual
            inyectado_anual += inversion_extra_mensual
        else:
            # MOMENTO DE INDEPENDENCIA
            if renta_al_inicio_independencia == 0:
                renta_al_inicio_independencia = renta_proyectada
            
            capital_actual -= renta_proyectada
            total_pagado_renta += renta_proyectada
            retiro_anual += renta_proyectada
            
            meses_solo = meses_desde_meta - periodo_gracia_meses
            if meses_solo == 1 or (meses_solo > 1 and meses_solo % 24 == 0):
                capital_actual -= gasto_buffer_proyectado
                retiro_anual += gasto_buffer_proyectado
    
    capital_actual += capital_actual * (rendimiento_anual / 12)
    if capital_actual <= 0 and año_agotamiento is None: año_agotamiento = año_actual

    if mes % 12 == 0:
        es_solo = meta_lograda and (mes - mes_de_la_meta > (años_extra_trabajo * 12))
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital_actual) if capital_actual > 0 else 0,
            "Renta Mens.": round(renta_proyectada) if es_solo else 0,
            "Total Renta Acum.": round(total_pagado_renta),
            "Inyectado ($)": round(inyectado_anual),
            "Retiro ($)": round(retiro_anual),
            "Status": "Viviendo Solo 🏠" if es_solo else "Con Padres 👨‍👩‍👦"
        })
        inyectado_anual = 0 ; retiro_anual = 0

df = pd.DataFrame(datos)

# 4. Layout
col_table, col_chart = st.columns([1.1, 0.9])
with col_table:
    st.subheader("📑 Simulación de Independencia")
    st.dataframe(df.drop(columns=['Total Renta Acum.']).style.format({
        "Año": "{:.0f}", "Capital ($)": "{:,.0f}", 
        "Inyectado ($)": "{:,.0f}", "Retiro ($)": "{:,.0f}"
    }), height=400, use_container_width=True, hide_index=True)

with col_chart:
    st.subheader("📈 Capital vs Gasto en Libertad")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='#00d1b2', width=3)))
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Total Renta Acum.'], name="Renta Pagada (Rojo)", line=dict(color='#ff4b4b')))
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=20,b=0), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

# 5. KPIs
st.markdown("---")
k1, k2, k3 = st.columns(3)
k1.metric(f"Capital Final ({año_final_proy})", f"${capital_actual:,.0f}")
k2.metric(f"Monto del buffer a 2 Años (Hoy)", f"${retiro_buffer_hoy:,.0f}")
k3.metric("Total Renta Pagada (Vida Solo)", f"${total_pagado_renta:,.0f}")

if meta_lograda:
    usa_plan = años_extra_trabajo > 0
    año_independencia = año_meta + (años_extra_trabajo if usa_plan else 0)
    if año_agotamiento:
        st.warning(f"⚠️ **Alerta:** Podrías salir de casa en {año_independencia}, pero el dinero se agota en {año_agotamiento}.")
    else:
        st.info(f"🚀\n\n**Libertad Lograda:** Puedes independizarte en **{año_independencia}**. Tu capital soportará la renta y gastos hasta el {año_final_proy}.")

st.markdown("---")
m1, m2 = st.columns(2)
m1.markdown(f"<p style='font-size:16px; margin-bottom:0px;'>🟢 Renta al salir de casa ({año_independencia if meta_lograda else '?'})</p><p style='font-size:24px; color:#28a745; font-weight:bold; margin-top:0px;'>${renta_al_inicio_independencia:,.0f}/mes</p>", unsafe_allow_html=True)
m2.markdown(f"<p style='font-size:16px; margin-bottom:0px;'>🔴 Renta proyectada al final ({año_final_proy})</p><p style='font-size:24px; color:#ff4b4b; font-weight:bold; margin-top:0px;'>${renta_proyectada:,.0f}/mes</p>", unsafe_allow_html=True)
