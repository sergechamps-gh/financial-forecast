import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración de tiempo dinámica
YEAR_ACTUAL = datetime.now().year

st.set_page_config(page_title=f"Serge Financial Strategy v3.42", layout="wide")
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
    
    st.header("🎯 Meta de Retiro")
    liquidez_deseada = st.number_input("Liquidez deseada despues de la compra ($)", value=500000, step=10000)
    
    st.header("💸 Fase de Desembolso")
    retiro_buffer_hoy = st.number_input(f"Monto del gasto bianual para vivir de inversiones (valor {YEAR_ACTUAL} $)", value=60000, step=5000)
    inflacion_gastos = st.number_input("Inflación de gastos (%)", value=3.0, step=0.5) / 100
    
    años_proyeccion = st.slider("Cantidad de años para vivir de inversiones", 4, 60, 48)

    st.header("🛡️ Plan de Contingencia")
    años_extra_trabajo = st.slider("Años extra de trabajo post-compra si la meta no se cumple", 0, 15, 0)
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
año_agotamiento = None
costo_final_aparta = 0
capital_post_meta = 0

inyectado_anual = 0
retiro_anual = 0

# Fila Génesis
datos.append({
    "Año": YEAR_ACTUAL, "Capital ($)": round(cap_inicial), "Precio Apt": f"{round(precio_hoy):,}",
    "Inyectado ($)": 0, "Retiro ($)": 0, 
    "Gasto_2Y": round(retiro_buffer_hoy), "Status": "Inicio 🚀"
})

for mes in range(1, meses + 1):
    año_actual = YEAR_ACTUAL + (mes // 12)
    nombre_mes_actual = MESES_NOMBRES[(mes % 12) - 1]
    
    if not meta_lograda:
        precio_aparta *= (1 + (inflacion_inmueble / 12))
    gasto_buffer_ajustado *= (1 + (inflacion_gastos / 12))

    if not meta_lograda and capital_actual >= (precio_aparta + liquidez_deseada):
        meta_lograda = True
        año_meta = año_actual
        mes_nombre_meta = nombre_mes_actual
        mes_de_la_compra = mes
        costo_final_aparta = precio_aparta
        
        usa_plan = años_extra_trabajo > 0 and inversion_extra_mensual > 0
        gasto_inicial = precio_aparta + (gasto_buffer_ajustado if not usa_plan else 0)
        
        capital_actual -= gasto_inicial
        capital_post_meta = capital_actual
        retiro_anual += gasto_inicial
    
    if not meta_lograda:
        capital_actual += ahorro_mensual
        inyectado_anual += ahorro_mensual
    else:
        meses_desde_compra = mes - mes_de_la_compra
        usa_plan = años_extra_trabajo > 0 and inversion_extra_mensual > 0
        es_periodo_extra = usa_plan and meses_desde_compra <= (años_extra_trabajo * 12)
        
        if es_periodo_extra:
            capital_actual += inversion_extra_mensual
            inyectado_anual += inversion_extra_mensual
        else:
            periodo_gracia = (años_extra_trabajo * 12) if usa_plan else 0
            meses_post_trabajo = meses_desde_compra - periodo_gracia
            
            if meses_post_trabajo == 1 or (meses_post_trabajo > 1 and meses_post_trabajo % 24 == 0):
                capital_actual -= gasto_buffer_ajustado
                retiro_anual += gasto_buffer_ajustado
    
    rendimiento_mes = capital_actual * (rendimiento_anual / 12)
    capital_actual += rendimiento_mes

    if capital_actual <= 0 and año_agotamiento is None:
        año_agotamiento = año_actual

    if mes % 12 == 0:
        periodo_gracia = (años_extra_trabajo * 12) if (años_extra_trabajo > 0 and inversion_extra_mensual > 0) else 0
        es_retiro = meta_lograda and (mes - mes_de_la_compra > periodo_gracia)
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital_actual) if capital_actual > 0 else 0,
            "Precio Apt": "COMPRADO" if meta_lograda else f"{round(precio_aparta):,}",
            "Inyectado ($)": round(inyectado_anual),
            "Retiro ($)": round(retiro_anual),
            "Gasto_2Y": round(gasto_buffer_ajustado),
            "Status": "Retiro 🌴" if es_retiro else "Activo 💼"
        })
        inyectado_anual = 0; retiro_anual = 0

df = pd.DataFrame(datos)

# 4. Layout
col_table, col_chart = st.columns([1.2, 0.8])
with col_table:
    st.subheader(f"📑 Proyección a {años_proyeccion} Años")
    st.dataframe(
        df.drop(columns=['Gasto_2Y']).style.format({
            "Año": "{:.0f}", "Capital ($)": "{:,.0f}", 
            "Inyectado ($)": "{:,.0f}", "Retiro ($)": "{:,.0f}"
        }), 
        height=400, use_container_width=True, hide_index=True
    )

with col_chart:
    st.subheader("📈 Capital vs Gasto")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='royalblue', width=3)))
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Gasto_2Y'], name="Gasto (2Y)", line=dict(color='orange', dash='dot')))
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=20, b=0), template="plotly_dark", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

# 5. KPIs y Banners
st.markdown("---")
año_final_proy = YEAR_ACTUAL + años_proyeccion
k1, k2, k3 = st.columns(3)
with k1: st.metric(f"Capital Final ({año_final_proy})", f"${df['Capital ($)'].iloc[-1]:,}")
with k2: st.metric(f"Monto del buffer a 2 Años (Hoy {YEAR_ACTUAL})", f"${retiro_buffer_hoy:,}")
with k3: 
    if meta_lograda: st.success(f"🎯 Compra realizada en {mes_nombre_meta} {año_meta}")
    else: st.error("🎯 Meta No Alcanzada")

if meta_lograda:
    usa_plan = años_extra_trabajo > 0 and inversion_extra_mensual > 0
    año_libertad = año_meta + (años_extra_trabajo if usa_plan else 0)
    
    if año_agotamiento:
        contexto_plan = f" y haber trabajado {años_extra_trabajo} años más invirtiendo ${inversion_extra_mensual:,} al mes," if usa_plan else ","
        st.warning(f"⚠️\n\n**Alerta de Sistema:** Después de la compra en {mes_nombre_meta} {año_meta}{contexto_plan} el capital se agota en el año **{año_agotamiento}**.")
    else:
        inicio_texto = f"Apartamento comprado en {mes_nombre_meta} de {año_meta}"
        if usa_plan:
            inicio_texto += f" y retiro iniciado en {mes_nombre_meta} de **{año_libertad}**"
        else:
            inicio_texto += " y retiro iniciado inmediatamente"
        st.info(f"🚀\n\n**Libertad Financiera Lograda:** {inicio_texto}. Sostenible hasta el año **{año_final_proy}**.")

    st.markdown("---")
    m1, m2 = st.columns(2)
    m1.markdown(f"<p style='font-size:16px; margin-bottom:0px;'>🏠 Costo Final Apartamento</p><p style='font-size:24px; color:#ff4b4b; font-weight:bold; margin-top:0px;'>${costo_final_aparta:,.0f}</p>", unsafe_allow_html=True)
    m2.markdown(f"<p style='font-size:16px; margin-bottom:0px;'>💰 Capital Post-Compra</p><p style='font-size:24px; color:#28a745; font-weight:bold; margin-top:0px;'>${capital_post_meta:,.0f}</p>", unsafe_allow_html=True)
