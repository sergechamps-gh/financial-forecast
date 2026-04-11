import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración inicial
YEAR_ACTUAL = datetime.now().year
st.set_page_config(page_title="Serge Financial Strategy v4.5.9", layout="wide")
st.title("Dashboard: Libertad Financiera")

MESES_NOMBRES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# Inicializamos año_meta en el estado de la sesión para el slider
if 'año_meta_cache' not in st.session_state:
    st.session_state.año_meta_cache = YEAR_ACTUAL + 5 

# 2. Sidebar
with st.sidebar:
    st.header("⚙️ Variables")
    cap_inicial = st.number_input("Capital Inicial ($)", value=135000, step=5000)
    ahorro_mensual = st.number_input("Aporte Mensual ($)", value=2000, step=100)
    rendimiento_anual = st.number_input("Rendimiento del Mercado (%)", value=10.0, step=0.5) / 100
    
    st.header("🏠 Precio Inmueble")
    precio_hoy = st.number_input("Precio Maximo Hoy ($)", value=180000, step=5000)
    inflacion_inmueble = st.number_input("Inflación Inmueble (%)", value=4.0, step=0.5) / 100
    
    st.subheader("🏢 Gastos de Condominio")
    cuota_condo_hoy = st.number_input("Cuota mensual actual ($)", value=250, step=50)
    inflacion_condo = st.number_input("Incremento anual cuota (%)", value=5.0, step=0.5) / 100

    st.header("🎯 Meta de Retiro")
    liquidez_deseada = st.number_input("Liquidez deseada despues de la compra ($)", value=300000, step=10000)
    
    st.header("💸 Fase de Desembolso")
    retiro_buffer_hoy = st.number_input(f"Monto gasto bianual (valor {YEAR_ACTUAL} $)", value=60000, step=5000)
    inflacion_gastos = st.number_input("Inflación de gastos (%)", value=3.0, step=0.5) / 100
    
    años_proyeccion = st.slider("Cantidad de años de proyección total", 10, 80, 60)

    st.header("🛡️ Plan de Contingencia")
    # SLIDER DINÁMICO: Muestra el año final basado en el cálculo previo
    año_fin_est = st.session_state.año_meta_cache
    años_extra_trabajo = st.slider(f"Años extra post-compra (Termina en: {año_fin_est + 1 if 'años_extra' not in locals() else año_fin_est + años_extra_trabajo})", 0, 15, 1)
    inversion_extra_mensual = st.number_input("Inversión mensual extra post-compra ($)", value=0, step=100)

# 3. Motor de Cálculo
meses = años_proyeccion * 12
datos = []
capital_actual = cap_inicial
precio_aparta = precio_hoy
meta_lograda = False
año_meta = YEAR_ACTUAL
mes_nombre_meta = ""
mes_de_la_compra = -1
gasto_buffer_ajustado = retiro_buffer_hoy 
cuota_condo_ajustada = cuota_condo_hoy
año_agotamiento = None
costo_final_aparta = 0
capital_post_meta = 0
capital_post_laboral = 0 

total_ahorro_propio = cap_inicial
total_intereses_generados = 0
inyectado_anual = 0
retiro_buffer_anual = 0 
condo_anual_acumulado = 0

for mes in range(1, meses + 1):
    año_actual = YEAR_ACTUAL + (mes // 12)
    if not meta_lograda:
        precio_aparta *= (1 + (inflacion_inmueble / 12))
    
    gasto_buffer_ajustado *= (1 + (inflacion_gastos / 12))
    cuota_condo_ajustada *= (1 + (inflacion_condo / 12))

    if not meta_lograda and capital_actual >= (precio_aparta + liquidez_deseada):
        meta_lograda = True
        año_meta = año_actual
        st.session_state.año_meta_cache = año_meta # Guardamos para el slider
        mes_nombre_meta = MESES_NOMBRES[(mes % 12) - 1]
        mes_de_la_compra = mes
        costo_final_aparta = precio_aparta
        capital_actual -= precio_aparta
        capital_post_meta = capital_actual
        retiro_buffer_anual += precio_aparta

    if not meta_lograda:
        capital_actual += ahorro_mensual
        inyectado_anual += ahorro_mensual
        total_ahorro_propio += ahorro_mensual
    else:
        capital_actual -= cuota_condo_ajustada
        condo_anual_acumulado += cuota_condo_ajustada
        meses_desde_compra = mes - mes_de_la_compra
        es_periodo_extra = meses_desde_compra <= (años_extra_trabajo * 12)
        
        if es_periodo_extra:
            capital_actual += inversion_extra_mensual
            inyectado_anual += inversion_extra_mensual
            total_ahorro_propio += inversion_extra_mensual
            if meses_desde_compra == (años_extra_trabajo * 12):
                capital_post_laboral = capital_actual
        else:
            meses_post_trabajo = meses_desde_compra - (años_extra_trabajo * 12)
            if meses_post_trabajo == 1 or (meses_post_trabajo > 1 and meses_post_trabajo % 24 == 0):
                capital_actual -= gasto_buffer_ajustado
                retiro_buffer_anual += gasto_buffer_ajustado
    
    interes_mes = capital_actual * (rendimiento_anual / 12)
    total_intereses_generados += interes_mes
    capital_actual += interes_mes
    if capital_actual <= 0 and año_agotamiento is None:
        año_agotamiento = año_actual

    if mes % 12 == 0:
        es_retiro_status = meta_lograda and (mes - mes_de_la_compra > (años_extra_trabajo * 12))
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital_actual) if capital_actual > 0 else 0,
            "Precio Apt": "COMPRADO" if meta_lograda else f"{round(precio_aparta):,}",
            "Inyectado ($)": round(inyectado_anual),
            "Retiro ($)": round(retiro_buffer_anual),
            "Condo ($)": round(condo_anual_acumulado),
            "Condo_Mes_Graf": round(cuota_condo_ajustada),
            "Gasto_Vida_Graf": round(gasto_buffer_ajustado),
            "Status": "Retiro 🌴" if es_retiro_status else "Activo 💼"
        })
        inyectado_anual = 0; retiro_buffer_anual = 0; condo_anual_acumulado = 0

if años_extra_trabajo == 0:
    capital_post_laboral = capital_post_meta

df = pd.DataFrame(datos)

# 4. Layout
col_table, col_chart = st.columns([1.2, 0.8])
with col_table:
    st.subheader(f"🧬 Proyección a {años_proyeccion} Años")
    cols_a_mostrar = ['Año', 'Capital ($)', 'Retiro ($)', 'Status']
    st.dataframe(df[cols_a_mostrar].style.format({"Año": "{:.0f}", "Capital ($)": "{:,.0f}", "Retiro ($)": "{:,.0f}"}), height=400, use_container_width=True, hide_index=True)

with col_chart:
    st.subheader("📈 Evolución")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='#00d1b2', width=3)))
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=20, b=0), template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# 5. KPIs Finales
st.markdown("---")
m1, m2, m3 = st.columns(3)
año_libertad = año_meta + años_extra_trabajo if meta_lograda else YEAR_ACTUAL + años_proyeccion
m1.markdown(f"<p style='font-size:16px; margin-bottom:0px;'>🏠 Costo Inmueble</p><p style='font-size:24px; color:#ff4b4b; font-weight:bold; margin-top:0px;'>${costo_final_aparta:,.0f}</p>", unsafe_allow_html=True)
m2.markdown(f"<p style='font-size:16px; margin-bottom:0px;'>💰 Post-Compra</p><p style='font-size:24px; color:#28a745; font-weight:bold; margin-top:0px;'>${capital_post_meta:,.0f}</p>", unsafe_allow_html=True)
m3.markdown(f"<p style='font-size:16px; margin-bottom:0px;'>🏁 Post-Laboral ({año_libertad})</p><p style='font-size:24px; color:#1E90FF; font-weight:bold; margin-top:0px;'>${capital_post_laboral:,.0f}</p>", unsafe_allow_html=True)

st.markdown("---")
if meta_lograda:
    st.info(f"🚀 Plan: Compra en {mes_nombre_meta} {año_meta}. Retiro total en {año_libertad}.")
