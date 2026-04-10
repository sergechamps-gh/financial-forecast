import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy_financial as npf
from datetime import datetime

# 1. Configuración de tiempo dinámica
YEAR_ACTUAL = datetime.now().year

st.set_page_config(page_title=f"Serge Financial Strategy v4.6", layout="wide")
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
    
    st.subheader("🏢 Gastos de Condominio (HOA)")
    cuota_condo_hoy = st.number_input(f"Cuota mensual actual ($)", value=250, step=50)
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
meta_lograda = False
año_meta = None
mes_nombre_meta = ""
mes_de_la_compra = -1
año_agotamiento = None
costo_final_aparta = 0
capital_post_meta = 0

total_ahorro_propio = cap_inicial
total_intereses_generados = 0

inyectado_anual = 0
retiro_anual = 0
condo_anual_acumulado = 0

for mes in range(1, meses + 1):
    # Calculamos en qué año de la proyección estamos (Año 0, 1, 2...)
    años_transcurridos = mes // 12
    año_actual = YEAR_ACTUAL + años_transcurridos
    nombre_mes_actual = MESES_NOMBRES[(mes % 12) - 1]
    
    # Precios ajustados con inflación ANUAL (no mensual compuesta)
    precio_aparta_inflado = precio_hoy * ((1 + inflacion_inmueble) ** años_transcurridos)
    gasto_buffer_inflado = retiro_buffer_hoy * ((1 + inflacion_gastos) ** años_transcurridos)
    cuota_condo_mensual_inflada = cuota_condo_hoy * ((1 + inflacion_condo) ** años_transcurridos)

    # Condición de compra
    if not meta_lograda and capital_actual >= (precio_aparta_inflado + liquidez_deseada):
        meta_lograda = True
        año_meta = año_actual
        mes_nombre_meta = nombre_mes_actual
        mes_de_la_compra = mes
        costo_final_aparta = precio_aparta_inflado
        capital_actual -= precio_aparta_inflado
        capital_post_meta = capital_actual
        retiro_anual += precio_aparta_inflado

    # Lógica de Flujo de Caja
    if not meta_lograda:
        capital_actual += ahorro_mensual
        inyectado_anual += ahorro_mensual
        total_ahorro_propio += ahorro_mensual
    else:
        # Pagar HOA Mensual
        capital_actual -= cuota_condo_mensual_inflada
        condo_anual_acumulado += cuota_condo_mensual_inflada
        retiro_anual += cuota_condo_mensual_inflada

        meses_desde_compra = mes - mes_de_la_compra
        es_periodo_extra = meses_desde_compra <= (años_extra_trabajo * 12)
        
        if es_periodo_extra:
            capital_actual += inversion_extra_mensual
            inyectado_anual += inversion_extra_mensual
            total_ahorro_propio += inversion_extra_mensual
        else:
            meses_post_trabajo = meses_desde_compra - (años_extra_trabajo * 12)
            # Retiro de Buffer cada 2 años (24 meses)
            if meses_post_trabajo == 1 or (meses_post_trabajo > 1 and meses_post_trabajo % 24 == 0):
                capital_actual -= gasto_buffer_inflado
                retiro_anual += gasto_buffer_inflado
    
    # Interés ganado mensualmente
    interes_mes = capital_actual * (rendimiento_anual / 12)
    total_intereses_generados += interes_mes
    capital_actual += interes_mes

    if capital_actual <= 0 and año_agotamiento is None:
        año_agotamiento = año_actual

    # Corte Anual para el DataFrame
    if mes % 12 == 0:
        es_retiro = meta_lograda and (mes - mes_de_la_compra > (años_extra_trabajo * 12))
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital_actual) if capital_actual > 0 else 0,
            "Precio Apt": "COMPRADO" if meta_lograda else f"{round(precio_aparta_inflado):,}",
            "Inyectado ($)": round(inyectado_anual),
            "Retiro ($)": round(retiro_anual),
            "Condo Anual ($)": round(condo_anual_acumulado) if meta_lograda else 0,
            "HOA_Mes_Graf": round(cuota_condo_mensual_inflada),
            "Buffer_Vida_Graf": round(gasto_buffer_inflado),
            "Status": "Retiro 🌴" if es_retiro else "Activo 💼"
        })
        inyectado_anual = 0; retiro_anual = 0; condo_anual_acumulado = 0

df = pd.DataFrame(datos)

# 4. Layout Principal
col_table, col_chart = st.columns([1.2, 0.8])
with col_table:
    st.subheader(f"📑 Proyección a {años_proyeccion} Años")
    st.dataframe(
        df.drop(columns=['HOA_Mes_Graf', 'Buffer_Vida_Graf']).style.format({
            "Año": "{:.0f}", "Capital ($)": "{:,.0f}", 
            "Inyectado ($)": "{:,.0f}", "Retiro ($)": "{:,.0f}", "Condo Anual ($)": "{:,.0f}"
        }), 
        height=450, use_container_width=True, hide_index=True
    )

with col_chart:
    st.subheader("📈 Capital vs Gastos (Anualizados)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='#00d1b2', width=3)))
    fig.add_trace(go.Scatter(x=df['Año'], y=df['HOA_Mes_Graf'] * 12, name="HOA (Anualizada)", line=dict(color='yellow', dash='dot')))
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Buffer_Vida_Graf'], name="Buffer Vida (2Y)", line=dict(color='orange', dash='dot')))
    
    fig.update_layout(height=450, margin=dict(l=0, r=0, t=20, b=0), template="plotly_dark", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

# 5. KPIs y Banners
st.markdown("---")
año_final_proy = YEAR_ACTUAL + años_proyeccion
k1, k2, k3 = st.columns(3)
with k1: st.metric(f"Capital Final ({año_final_proy})", f"${df['Capital ($)'].iloc[-1]:,}")
with k2: st.metric(f"Monto del buffer a 2 Años (Hoy)", f"${retiro_buffer_hoy:,}")
with k3: 
    if meta_lograda: st.success(f"🎯 Compra realizada en {mes_nombre_meta} {año_meta}")
    else: st.error("🎯 Meta No Alcanzada")

if meta_lograda:
    año_libertad = año_meta + años_extra_trabajo
    if año_agotamiento:
        msg_warn = f"⚠️ **Alerta de Sistema:** Capital agotado en **{año_agotamiento}**. Revisa el plan."
        st.warning(msg_warn)
    else:
        st.info(f"🚀 **Libertad Financiera Lograda:** Retiro inicia en {mes_nombre_meta} {año_libertad}.")

st.markdown("---")
m1, m2 = st.columns(2)
m1.markdown(f"🏠 Costo Final Apartamento: **${costo_final_aparta:,.0f}**")
m2.markdown(f"💰 Capital Post-Compra: **${capital_post_meta:,.0f}**")

# 6. Auditoría
st.markdown("---")
st.markdown("### 📊 Eficiencia del Plan")
c1, c2, c3 = st.columns(3)
c1.metric("Ahorro Propio", f"${round(total_ahorro_propio):,}")
c2.metric("Intereses Generados", f"${round(total_intereses_generados):,}")
c3.metric("Multiplicador", f"{round(total_intereses_generados / total_ahorro_propio, 2)}x")
