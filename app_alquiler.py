import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración
YEAR_ACTUAL = datetime.now().year
st.set_page_config(page_title="Serge Rental Strategy v1.1", layout="wide")
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

inyectado_anual = 0 ; retiro_anual = 0

# Fila Inicio
datos.append({
    "Año": YEAR_ACTUAL, "Capital ($)": round(cap_inicial), "Renta Mens.": round(renta_hoy),
    "Inyectado ($)": 0, "Retiro ($)": 0, "Status": "Inicio 🚀"
})

for mes in range(1, meses + 1):
    año_actual = YEAR_ACTUAL + (mes // 12)
    nombre_mes_actual = MESES_NOMBRES[mes % 12]
    
    renta_actualizada *= (1 + (inflacion_renta / 12))
    gasto_buffer_ajustado *= (1 + (inflacion_gastos / 12))

    if not meta_lograda and capital_actual >= liquidez_deseada:
        meta_lograda = True
        año_meta = año_actual
        mes_nombre_meta = nombre_mes_actual
        mes_de_la_meta = mes

    if not meta_lograda:
        capital_actual += ahorro_mensual
        inyectado_anual += ahorro_mensual
    else:
        # Lógica de Contingencia
        meses_desde_meta = mes - mes_de_la_meta
        usa_plan = años_extra_trabajo > 0
        es_periodo_extra = usa_plan and meses_desde_meta <= (años_extra_trabajo * 12)
        
        if es_periodo_extra:
            capital_actual += inversion_extra_mensual
            inyectado_anual += inversion_extra_mensual
        else:
            # Pagar Renta Mensual
            capital_actual -= renta_actualizada
            retiro_anual += renta_actualizada
            # Pagar Gasto Bianual (cada 24 meses de retiro real)
            periodo_gracia = (años_extra_trabajo * 12) if usa_plan else 0
            meses_post_trabajo = meses_desde_meta - periodo_gracia
            if meses_post_trabajo == 1 or (meses_post_trabajo > 1 and meses_post_trabajo % 24 == 0):
                capital_actual -= gasto_buffer_ajustado
                retiro_anual += gasto_buffer_ajustado
    
    capital_actual += capital_actual * (rendimiento_anual / 12)
    if capital_actual <= 0 and año_agotamiento is None: año_agotamiento = año_actual

    if mes % 12 == 0:
        periodo_gracia = (años_extra_trabajo * 12) if años_extra_trabajo > 0 else 0
        es_retiro = meta_lograda and (mes - mes_de_la_meta > periodo_gracia)
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

# 4. Layout
col_table, col_chart = st.columns([1.2, 0.8])
with col_table:
    st.subheader(f"📑 Simulación Renta vs Capital")
    st.dataframe(df.style.format({
        "Año": "{:.0f}", "Capital ($)": "{:,.0f}", 
        "Inyectado ($)": "{:,.0f}", "Retiro ($)": "{:,.0f}"
    }), height=450, use_container_width=True, hide_index=True)

with col_chart:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='#00d1b2', width=3)))
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig, use_container_width=True)

# 5. Banners de Análisis
st.markdown("---")
if meta_lograda:
    usa_plan = años_extra_trabajo > 0
    año_libertad = año_meta + (años_extra_trabajo if usa_plan else 0)
    if año_agotamiento:
        st.warning(f"⚠️ **Alerta:** Alcanzas la meta en {mes_nombre_meta} {año_meta}, pero con este nivel de gasto el capital muere en **{año_agotamiento}**. Sugerencia: Sube los años extra de trabajo o el rendimiento.")
    else:
        txt = f"Meta alcanzada en {mes_nombre_meta} {año_meta}"
        if usa_plan: txt += f" y retiro iniciado en {año_libertad} tras periodo extra de inversión."
        else: txt += " y retiro iniciado de inmediato."
        st.info(f"🚀 **Libertad Financiera Lograda:** {txt} Sostenible hasta **{año_final_proy}**.")
