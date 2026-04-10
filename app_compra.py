import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración
YEAR_ACTUAL = datetime.now().year
st.set_page_config(page_title="Serge Financial Strategy v4.9", layout="wide")
st.title("🧬 Dashboard de Libertad Financiera (Compra)")

MESES_NOMBRES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# 2. Sidebar
with st.sidebar:
    st.header("⚙️ Variables")
    cap_inicial = st.number_input("Capital Inicial ($)", value=135000, step=5000)
    ahorro_mensual = st.number_input("Aporte Mensual ($)", value=2000, step=100)
    rendimiento_anual = st.number_input("Rendimiento del Mercado (%)", value=10.0, step=0.5) / 100
    
    st.header("🏠 Inmueble")
    precio_hoy = st.number_input(f"Precio hoy ($)", value=200000, step=5000)
    inflacion_inmueble = st.number_input("Inflación Inmueble (%)", value=4.0, step=0.5) / 100
    
    st.subheader("🏢 Gastos de Condominio")
    cuota_condo_hoy = st.number_input(f"Cuota mensual actual ($)", value=250, step=50)
    inflacion_condo = st.number_input("Incremento anual cuota (%)", value=5.0, step=0.5) / 100

    st.header("🎯 Meta de Retiro")
    liquidez_deseada = st.number_input("Liquidez deseada post-compra ($)", value=300000, step=10000)
    retiro_buffer_hoy = st.number_input("Monto gasto bianual (hoy $)", value=60000, step=5000)
    inflacion_gastos = st.number_input("Inflación de gastos (%)", value=3.0, step=0.5) / 100
    
    años_proyeccion = st.slider("Años de proyección total", 10, 80, 60)
    años_extra_trabajo = st.slider("Años extra de trabajo post-compra", 0, 15, 1)
    inversion_extra_mensual = st.number_input("Inversión mensual extra ($)", value=0, step=100)

# 3. Motor de Cálculo
meses = años_proyeccion * 12
datos = []
capital_actual = cap_inicial
meta_lograda = False
año_meta = None
mes_de_la_compra = -1
año_agotamiento = None
costo_final_aparta = 0

total_ahorro_propio = cap_inicial
total_intereses_generados = 0

inyectado_anual = 0; retiro_anual = 0; condo_anual_acumulado = 0

for mes in range(1, meses + 1):
    # CÁLCULO DE INFLACIÓN ANUAL (Step-based)
    # Esto evita que la cuota suba todos los meses
    años_transcurridos = mes // 12
    año_actual = YEAR_ACTUAL + años_transcurridos
    
    # Precios proyectados al año actual
    precio_aparta_iter = precio_hoy * ((1 + inflacion_inmueble) ** años_transcurridos)
    gasto_buffer_iter = retiro_buffer_hoy * ((1 + inflacion_gastos) ** años_transcurridos)
    cuota_condo_iter = cuota_condo_hoy * ((1 + inflacion_condo) ** años_transcurridos)

    # Lógica de Compra
    if not meta_lograda and capital_actual >= (precio_aparta_iter + liquidez_deseada):
        meta_lograda = True
        año_meta = año_actual
        mes_de_la_compra = mes
        costo_final_aparta = precio_aparta_iter
        capital_actual -= precio_aparta_iter

    # Flujos
    if not meta_lograda:
        capital_actual += ahorro_mensual
        inyectado_anual += ahorro_mensual
        total_ahorro_propio += ahorro_mensual
    else:
        # Gastos operativos
        capital_actual -= cuota_condo_iter
        condo_anual_acumulado += cuota_condo_iter
        retiro_anual += cuota_condo_iter

        meses_desde_compra = mes - mes_de_la_compra
        if meses_desde_compra <= (años_extra_trabajo * 12):
            capital_actual += inversion_extra_mensual
            inyectado_anual += inversion_extra_mensual
            total_ahorro_propio += inversion_extra_mensual
        else:
            meses_post_trabajo = meses_desde_compra - (años_extra_trabajo * 12)
            if meses_post_trabajo == 1 or (meses_post_trabajo > 1 and meses_post_trabajo % 24 == 0):
                capital_actual -= gasto_buffer_iter
                retiro_anual += gasto_buffer_iter
    
    # Rendimiento
    interes_mes = capital_actual * (rendimiento_anual / 12)
    capital_actual += interes_mes
    total_intereses_generados += interes_mes

    if capital_actual <= 0 and año_agotamiento is None:
        año_agotamiento = año_actual

    if mes % 12 == 0:
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital_actual) if capital_actual > 0 else 0,
            "Precio Apt": "COMPRADO" if meta_lograda else f"{round(precio_aparta_iter):,}",
            "Inyectado ($)": round(inyectado_anual),
            "Retiro ($)": round(retiro_anual),
            "Condo ($)": round(condo_anual_acumulado) if meta_lograda else 0,
            "Condo_Mes_Graf": round(cuota_condo_iter),
            "Gasto_Vida_Graf": round(gasto_buffer_iter)
        })
        inyectado_anual = 0; retiro_anual = 0; condo_anual_acumulado = 0

df = pd.DataFrame(datos)

# 4. Layout
col_table, col_chart = st.columns([1.2, 0.8])
with col_table:
    st.subheader("📑 Proyección Anual")
    st.dataframe(df.drop(columns=['Condo_Mes_Graf', 'Gasto_Vida_Graf']).style.format({"Año": "{:.0f}", "Capital ($)": "{:,.0f}"}), hide_index=True)

with col_chart:
    st.subheader("📈 Escala de Gastos")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='#00d1b2', width=3)))
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Condo_Mes_Graf'] * 12, name="Condo (Anual)", line=dict(color='yellow', dash='dot')))
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Gasto_Vida_Graf'], name="Buffer Vida (2Y)", line=dict(color='orange', dash='dot')))
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

if meta_lograda:
    st.success(f"🎯 Compra en {año_meta} | Costo: ${costo_final_aparta:,.0f} | HOA inicial: ${round(cuota_condo_hoy * ((1 + inflacion_condo) ** (mes_de_la_compra // 12)))}/mes")
