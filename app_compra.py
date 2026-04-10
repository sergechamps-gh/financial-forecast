import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

YEAR_ACTUAL = datetime.now().year

st.set_page_config(page_title="Serge Financial Strategy v4.7", layout="wide")
st.title("🧬 Dashboard de Libertad Financiera (Compra)")

MESES_NOMBRES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

with st.sidebar:
    st.header("⚙️ Variables")
    cap_inicial = st.number_input("Capital Inicial ($)", value=135000, step=5000)
    ahorro_mensual = st.number_input("Aporte Mensual ($)", value=2000, step=100)
    rendimiento_anual = st.number_input("Rendimiento del Mercado (%)", value=10.0, step=0.5) / 100
    
    st.header("🏠 Inmueble")
    precio_hoy = st.number_input(f"Precio del aparta ($)", value=200000, step=5000)
    inflacion_inmueble = st.number_input("Inflación Inmueble (%)", value=4.0, step=0.5) / 100
    
    st.subheader("🏢 Gastos de Condominio")
    cuota_condo_hoy = st.number_input(f"Cuota mensual hoy ($)", value=400, step=50)
    inflacion_condo = st.number_input("Incremento anual cuota (%)", value=5.0, step=0.5) / 100

    st.header("🎯 Meta de Retiro")
    liquidez_deseada = st.number_input("Liquidez deseada post-compra ($)", value=300000, step=10000)
    
    st.header("💸 Fase de Desembolso")
    retiro_buffer_hoy = st.number_input(f"Monto buffer bianual (valor hoy $)", value=60000, step=5000)
    inflacion_gastos = st.number_input("Inflación de gastos (%)", value=3.0, step=0.5) / 100
    
    años_proyeccion = st.slider("Años de proyección", 10, 80, 60)
    años_extra_trabajo = st.slider("Años extra trabajo post-compra", 0, 15, 1)

# Motor de Cálculo
meses = años_proyeccion * 12
datos = []
capital_actual = cap_inicial
meta_lograda = False
año_meta = None
mes_nombre_meta = ""
mes_de_la_compra = -1
año_agotamiento = None
costo_final_aparta = 0

inyectado_anual = 0
retiro_anual = 0
condo_anual_acumulado = 0

for mes in range(1, meses + 1):
    # Calculamos inflación por año entero (evita el crecimiento mensual explosivo)
    año_progreso = mes // 12
    año_actual_cal = YEAR_ACTUAL + año_progreso
    
    precio_aparta_inflado = precio_hoy * ((1 + inflacion_inmueble) ** año_progreso)
    cuota_condo_mensual = cuota_condo_hoy * ((1 + inflacion_condo) ** año_progreso)
    buffer_vida_inflado = retiro_buffer_hoy * ((1 + inflacion_gastos) ** año_progreso)

    if not meta_lograda and capital_actual >= (precio_aparta_inflado + liquidez_deseada):
        meta_lograda = True
        año_meta = año_actual_cal
        mes_nombre_meta = MESES_NOMBRES[(mes % 12) - 1]
        mes_de_la_compra = mes
        costo_final_aparta = precio_aparta_inflado
        capital_actual -= precio_aparta_inflado

    if not meta_lograda:
        capital_actual += ahorro_mensual
        inyectado_anual += ahorro_mensual
    else:
        # Gastos post-compra
        capital_actual -= cuota_condo_mensual
        condo_anual_acumulado += cuota_condo_mensual
        retiro_anual += cuota_condo_mensual

        meses_desde_compra = mes - mes_de_la_compra
        if meses_desde_compra > (años_extra_trabajo * 12):
            meses_post_trabajo = meses_desde_compra - (años_extra_trabajo * 12)
            if meses_post_trabajo == 1 or (meses_post_trabajo > 1 and meses_post_trabajo % 24 == 0):
                capital_actual -= buffer_vida_inflado
                retiro_anual += buffer_vida_inflado
    
    # Interés ganado
    interes_mes = capital_actual * (rendimiento_anual / 12)
    capital_actual += interes_mes

    if capital_actual <= 0 and año_agotamiento is None:
        año_agotamiento = año_actual_cal

    if mes % 12 == 0:
        datos.append({
            "Año": año_actual_cal,
            "Capital ($)": round(capital_actual) if capital_actual > 0 else 0,
            "Precio Apt": "COMPRADO" if meta_lograda else f"{round(precio_aparta_inflado):,}",
            "Condo Mes ($)": round(cuota_condo_mensual),
            "Condo Anual ($)": round(condo_anual_acumulado) if meta_lograda else 0,
            "Retiro Total ($)": round(retiro_anual),
            "Status": "Retiro 🌴" if meta_lograda and (mes - mes_de_la_compra > (años_extra_trabajo * 12)) else "Activo 💼"
        })
        inyectado_anual = 0; retiro_anual = 0; condo_anual_acumulado = 0

df = pd.DataFrame(datos)

# Visualización
col1, col2 = st.columns([1.2, 0.8])
with col1:
    st.subheader("📑 Proyección Anual")
    st.dataframe(df.style.format({"Año": "{:.0f}", "Capital ($)": "{:,.0f}", "Condo Anual ($)": "{:,.0f}"}), use_container_width=True, hide_index=True)

with col2:
    st.subheader("📈 Progresión")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='#00d1b2', width=3)))
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Condo Mes ($)'] * 12, name="HOA Anual", line=dict(color='yellow', dash='dot')))
    fig.update_layout(template="plotly_dark", height=450)
    st.plotly_chart(fig, use_container_width=True)

if año_agotamiento:
    st.error(f"⚠️ El capital se agota en {año_agotamiento}")
elif meta_lograda:
    st.success(f"🎯 Compra en {mes_nombre_meta} {año_meta} por ${costo_final_aparta:,.0f}")
