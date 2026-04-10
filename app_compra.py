import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy_financial as npf
from datetime import datetime

# 1. Configuración de tiempo dinámica
YEAR_ACTUAL = datetime.now().year

st.set_page_config(page_title=f"Serge Financial Strategy v4.5", layout="wide")
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
    precio_hoy = st.number_input(f"Precio del aparta (en {YEAR_ACTUAL}) ($)", value=200000, step=5000)
    inflacion_inmueble = st.number_input("Inflación Inmueble (%)", value=4.0, step=0.5) / 100
    
    st.subheader("🏢 Gastos de Condominio")
    cuota_condo_hoy = st.number_input(f"Cuota mensual actual ($)", value=400, step=50)
    inflacion_condo = st.number_input("Incremento anual cuota (%)", value=5.0, step=0.5) / 100

    st.header("🎯 Meta de Retiro")
    liquidez_deseada = st.number_input("Liquidez deseada despues de la compra ($)", value=300000, step=10000)
    
    st.header("💸 Fase de Desembolso")
    retiro_buffer_hoy = st.number_input(f"Monto del gasto bianual para vivir (valor {YEAR_ACTUAL} $)", value=60000, step=5000)
    inflacion_gastos = st.number_input("Inflación de gastos (%)", value=3.0, step=0.5) / 100
    
    años_proyeccion = st.slider("Cantidad de años de proyección total", 10, 80, 60)

    st.header("🛡️ Plan de Contingencia")
    años_extra_trabajo = st.slider("Años extra de trabajo post-compra", 0, 15, 1)
    inversion_extra_mensual = st.number_input("Inversión mensual extra post-compra ($)", value=0, step=100)

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
cuota_condo_ajustada = cuota_condo_hoy
año_agotamiento = None
costo_final_aparta = 0
capital_post_meta = 0

total_ahorro_propio = cap_inicial
total_intereses_generados = 0

inyectado_anual = 0
retiro_anual = 0
condo_anual_acumulado = 0

for mes in range(1, meses + 1):
    año_actual = YEAR_ACTUAL + (mes // 12)
    nombre_mes_actual = MESES_NOMBRES[(mes % 12) - 1]
    
    # Ajustes ANUALES (Cada 12 meses)
    if mes % 12 == 0:
        if not meta_lograda:
            precio_aparta *= (1 + inflacion_inmueble)
        gasto_buffer_ajustado *= (1 + inflacion_gastos)
        cuota_condo_ajustada *= (1 + inflacion_condo)

    # Lógica de compra
    if not meta_lograda and capital_actual >= (precio_aparta + liquidez_deseada):
        meta_lograda = True
        año_meta = año_actual
        mes_nombre_meta = nombre_mes_actual
        mes_de_la_compra = mes
        costo_final_aparta = precio_aparta
        capital_actual -= precio_aparta
        capital_post_meta = capital_actual
        retiro_anual += precio_aparta

    if not meta_lograda:
        capital_actual += ahorro_mensual
        inyectado_anual += ahorro_mensual
        total_ahorro_propio += ahorro_mensual
    else:
        # Pagar cuota condominal (Mensual)
        capital_actual -= cuota_condo_ajustada
        condo_anual_acumulado += cuota_condo_ajustada
        retiro_anual += cuota_condo_ajustada

        meses_desde_compra = mes - mes_de_la_compra
        es_periodo_extra = meses_desde_compra <= (años_extra_trabajo * 12)
        
        if es_periodo_extra:
            capital_actual += inversion_extra_mensual
            inyectado_anual += inversion_extra_mensual
            total_ahorro_propio += inversion_extra_mensual
        else:
            meses_post_trabajo = meses_desde_compra - (años_extra_trabajo * 12)
            if meses_post_trabajo == 1 or (meses_post_trabajo > 1 and meses_post_trabajo % 24 == 0):
                capital_actual -= gasto_buffer_ajustado
                retiro_anual += gasto_buffer_ajustado
    
    # Rendimiento
    capital_actual += capital_actual * (rendimiento_anual / 12)
    total_intereses_generados += capital_actual * (rendimiento_anual / 12)

    if capital_actual <= 0 and año_agotamiento is None:
        año_agotamiento = año_actual

    if mes % 12 == 0:
        es_retiro = meta_lograda and (mes - mes_de_la_compra > (años_extra_trabajo * 12))
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital_actual) if capital_actual > 0 else 0,
            "Precio Apt": "COMPRADO" if meta_lograda else f"{round(precio_aparta):,}",
            "Inyectado ($)": round(inyectado_anual),
            "Retiro ($)": round(retiro_anual),
            "Condo Anual ($)": round(condo_anual_acumulado) if meta_lograda else 0,
            "Condo Mes ($)": round(cuota_condo_ajustada),
            "Gasto Vida (2Y)": round(gasto_buffer_ajustado),
            "Status": "Retiro 🌴" if es_retiro else "Activo 💼"
        })
        inyectado_anual = 0; retiro_anual = 0; condo_anual_acumulado = 0

df = pd.DataFrame(datos)

# 4. Layout
col_table, col_chart = st.columns([1.2, 0.8])
with col_table:
    st.subheader(f"📑 Proyección Anual")
    st.dataframe(
        df.drop(columns=['Condo Mes ($)', 'Gasto Vida (2Y)']).style.format({
            "Año": "{:.0f}", "Capital ($)": "{:,.0f}", 
            "Inyectado ($)": "{:,.0f}", "Retiro ($)": "{:,.0f}", "Condo Anual ($)": "{:,.0f}"
        }), 
        height=400, use_container_width=True, hide_index=True
    )

with col_chart:
    st.subheader("📈 Gastos Anualizados")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='#00d1b2', width=3)))
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Condo Mes ($)'] * 12, name="Condo (12m)", line=dict(color='yellow', dash='dot')))
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Gasto Vida (2Y)'], name="Buffer (2Y)", line=dict(color='orange', dash='dot')))
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=20, b=0), template="plotly_dark", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

# 5. KPIs y Banners (Misma lógica Serge)
st.markdown("---")
# ... (Banners omitidos por brevedad pero incluidos en el archivo real)
