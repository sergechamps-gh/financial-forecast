import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración
YEAR_ACTUAL = datetime.now().year
st.set_page_config(page_title="Serge Purchase Strategy v1.7", layout="wide")
st.title("🏠 Estrategia de Libertad Financiera (Compra)")

MESES_NOMBRES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# 2. Sidebar
with st.sidebar:
    st.header("⚙️ Fase de Acumulación")
    cap_inicial = st.number_input("Capital Inicial ($)", value=135000, step=5000)
    ahorro_mensual = st.number_input("Aporte Mensual ($)", value=2000, step=100)
    rendimiento_anual = st.number_input("Rendimiento Mercado (%)", value=10.0, step=0.5) / 100
    
    st.header("🏢 Inversión Inmobiliaria")
    precio_aparta = st.number_input("Precio del Apartamento ($)", value=250000, step=10000)
    gastos_cierre = st.number_input("Gastos de Cierre/Muebles ($)", value=20000, step=5000)
    
    st.header("🎯 Objetivo de Capital")
    liquidez_deseada = st.number_input("Liquidez Extra tras Compra ($)", value=500000, step=10000)
    
    st.header("💸 Costo de Vida (Post-Compra)")
    retiro_buffer_hoy = st.number_input(f"Gasto Bianual (SIN vivienda) (valor {YEAR_ACTUAL} $)", value=60000, step=5000)
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
compra_realizada = False
año_meta = None ; mes_nombre_meta = "" ; mes_de_la_meta = -1
año_agotamiento = None
gasto_buffer_proyectado = retiro_buffer_hoy
año_final_proy = YEAR_ACTUAL + años_proyeccion
costo_total_compra = precio_aparta + gastos_cierre

inyectado_anual = 0 ; retiro_anual = 0

for mes in range(1, meses + 1):
    año_actual = YEAR_ACTUAL + (mes // 12)
    gasto_buffer_proyectado *= (1 + (inflacion_gastos / 12))

    # Lógica de Meta (Llegar a: Precio Aparta + Liquidez Deseada)
    if not meta_lograda and capital_actual >= (costo_total_compra + liquidez_deseada):
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
        
        # Fase de Capitalización Extra
        if meses_desde_meta <= periodo_gracia_meses:
            capital_actual += inversion_extra_mensual
            inyectado_anual += inversion_extra_mensual
        else:
            # MOMENTO DE LA COMPRA E INDEPENDENCIA
            if not compra_realizada:
                capital_actual -= costo_total_compra
                compra_realizada = True
            
            # Retiros Bianuales de Vida
            meses_independencia = meses_desde_meta - periodo_gracia_meses
            if meses_independencia == 1 or (meses_independencia > 1 and meses_independencia % 24 == 0):
                capital_actual -= gasto_buffer_proyectado
                retiro_anual += gasto_buffer_proyectado
    
    capital_actual += capital_actual * (rendimiento_anual / 12)
    
    if capital_actual <= 0 and año_agotamiento is None:
        año_agotamiento = año_actual

    if mes % 12 == 0:
        es_independiente = compra_realizada
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital_actual), # Quitamos el tope de 0 para ver negativos
            "Inyectado ($)": round(inyectado_anual),
            "Retiro ($)": round(retiro_anual),
            "Status": "Independiente 🏠" if es_independiente else "Acumulación 💼"
        })
        inyectado_anual = 0 ; retiro_anual = 0

df = pd.DataFrame(datos)

# 4. Layout
col_table, col_chart = st.columns([1.1, 0.9])
with col_table:
    st.subheader("📑 Simulación de Independencia (Compra)")
    st.dataframe(df.style.format({
        "Año": "{:.0f}", "Capital ($)": "{:,.0f}", 
        "Inyectado ($)": "{:,.0f}", "Retiro ($)": "{:,.0f}"
    }), height=400, use_container_width=True, hide_index=True)

with col_chart:
    st.subheader("📈 Proyección de Capital")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='#00d1b2', width=3)))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig, use_container_width=True)

# 5. KPIs y Banners
st.markdown("---")
k1, k2, k3 = st.columns(3)
k1.metric(f"Capital Final ({año_final_proy})", f"${capital_actual:,.0f}")
k2.metric(f"Monto del Buffer (Hoy {YEAR_ACTUAL})", f"${retiro_buffer_hoy:,.0f}")
k3.metric("Costo Total Compra", f"${costo_total_compra:,.0f}")

if meta_lograda:
    usa_plan = años_extra_trabajo > 0
    año_compra = año_meta + (años_extra_trabajo if usa_plan else 0)
    
    if año_agotamiento:
        st.warning(f"⚠️\n\n**Hito Alcanzado pero Insuficiente:** Se logró el capital para comprar en **{año_meta}**, pero el remanente se agota en el año **{año_agotamiento}**. Necesitas más 'Liquidez Extra' o años de capitalización.")
    else:
        info_txt = f"Objetivo de ahorro logrado en {mes_nombre_meta} de {año_meta}"
        if usa_plan: info_txt += f" con compra e independencia en **{año_compra}**."
        else: info_txt += " con compra e independencia inmediata."
        st.info(f"🚀\n\n**Libertad Financiera Lograda:** {info_txt} Sostenible hasta el año **{año_final_proy}**.")
else:
    st.error(f"❌ **Meta no alcanzada:** No se logra el capital para compra + liquidez dentro del horizonte.")

