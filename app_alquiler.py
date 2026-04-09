import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración dinámica
YEAR_ACTUAL = datetime.now().year

st.set_page_config(page_title="Serge Financial Strategy v1.9", layout="wide")
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
    renta_hoy = st.number_input(f"Costo Alquiler Mensual (en {YEAR_ACTUAL}) ($)", value=1200, step=100)
    inflacion_renta = st.number_input("Inflación Alquiler Anual (%)", value=3.5, step=0.5) / 100
    
    st.header("🎯 Objetivo de Capital")
    liquidez_deseada = st.number_input("Capital Mínimo Requerido ($)", value=500000, step=10000)
    
    st.header("💸 Gastos de Vida")
    retiro_buffer_hoy = st.number_input(f"Gasto bianual (SIN renta) (valor {YEAR_ACTUAL} $)", value=60000, step=5000)
    inflacion_gastos = st.number_input("Inflación de Gastos (%)", value=3.0, step=0.5) / 100
    
    años_proyeccion = st.slider("Años de horizonte financiero", 4, 60, 48)

# 3. Motor de Cálculo
meses = años_proyeccion * 12
datos = []
capital_actual = cap_inicial
meta_lograda = False
año_meta = None ; mes_nombre_meta = ""
año_agotamiento = None
renta_actualizada = renta_hoy
gasto_buffer_ajustado = retiro_buffer_hoy
inyectado_anual = 0
retiro_bianual_log = 0 
meses_post_meta = 0

# Fila Génesis
datos.append({
    "Año": YEAR_ACTUAL, "Capital ($)": round(cap_inicial), 
    "Renta Mensual ($)": round(renta_hoy), "Inyectado ($)": 0, 
    "Retiro Buffer ($)": 0, "Buffer_Ref": round(retiro_buffer_hoy), "Status": "Inicio 🚀"
})

for mes in range(1, meses + 1):
    año_actual = YEAR_ACTUAL + (mes // 12)
    renta_actualizada *= (1 + (inflacion_renta / 12))
    gasto_buffer_ajustado *= (1 + (inflacion_gastos / 12))

    if not meta_lograda and capital_actual >= liquidez_deseada:
        meta_lograda = True
        año_meta = año_actual
        mes_nombre_meta = MESES_NOMBRES[mes % 12]

    if not meta_lograda:
        capital_actual += ahorro_mensual
        inyectado_anual += ahorro_mensual
    else:
        meses_post_meta += 1
        capital_actual -= renta_actualizada # Renta mensual (silenciosa)
        
        # Retiro Buffer cada 24 meses de libertad
        if meses_post_meta % 24 == 1: 
            capital_actual -= gasto_buffer_ajustado
            retiro_bianual_log += gasto_buffer_ajustado
    
    capital_actual += capital_actual * (rendimiento_anual / 12)

    if capital_actual <= 0 and año_agotamiento is None:
        año_agotamiento = año_actual

    if mes % 12 == 0:
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital_actual),
            "Renta Mensual ($)": round(renta_actualizada),
            "Inyectado ($)": round(inyectado_anual),
            "Retiro Buffer ($)": round(retiro_bianual_log),
            "Buffer_Ref": round(gasto_buffer_ajustado),
            "Status": "Libertad 🌴" if meta_lograda else "Acumulando 💼"
        })
        inyectado_anual = 0
        retiro_bianual_log = 0

df = pd.DataFrame(datos)

# 4. Layout
col_table, col_chart = st.columns([1, 1])
with col_table:
    st.subheader(f"📑 Auditoría de Flujo")
    st.dataframe(
        df.drop(columns=['Buffer_Ref']).style.format({
            "Año": "{:.0f}", "Capital ($)": "{:,.0f}", 
            "Renta Mensual ($)": "{:,.0f}", "Inyectado ($)": "{:,.0f}",
            "Retiro Buffer ($)": "{:,.0f}"
        }), height=500, use_container_width=True, hide_index=True
    )

with col_chart:
    st.subheader("📈 Evolución Financiera")
    fig = go.Figure()
    # Capital (Verde)
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='#00d1b2', width=3)))
    # Renta Anualizada (Rojo)
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Renta Mensual ($)'] * 12, name="Renta Anual", line=dict(color='#ff4b4b', dash='dot')))
    # Buffer de Referencia (Naranja)
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Buffer_Ref'], name="Costo Buffer 2Y", line=dict(color='orange', dash='dash')))
    
    fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0, r=0, t=20, b=0), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

# 5. Banners de Sostenibilidad (Restaurados)
st.markdown("---")
año_final = YEAR_ACTUAL + años_proyeccion

if meta_lograda:
    if año_agotamiento:
        st.warning(f"⚠️\n\n**Meta Alcanzada pero Insuficiente:** Se llegó a los ${liquidez_deseada:,.0f} en **{año_meta}**, pero el capital se agota en el año **{año_agotamiento}**. Necesitas ajustar el plan para cubrir el horizonte completo.")
    else:
        st.info(f"🚀\n\n**Libertad Financiera Lograda:** Meta alcanzada en {mes_nombre_meta} de {año_meta}. El capital es sostenible hasta el año **{año_final}**.")
else:
    st.error("❌ La meta de capital no se alcanza dentro del horizonte proyectado.")

# 6. KPIs
st.markdown("---")
k1, k2, k3 = st.columns(3)
with k1: st.metric(f"Capital Final ({año_final})", f"${df['Capital ($)'].iloc[-1]:,}")
with k2: st.metric(f"Aporte Mensual", f"${ahorro_mensual:,}")
with k3: 
    if meta_lograda: st.success(f"🎯 Meta lograda en {año_meta}")
    else: st.error("🎯 Meta No Alcanzada")

m1, m2 = st.columns(2)
m1.markdown(f"<p style='font-size:16px; margin-bottom:0px;'>🟢 Renta Mensual Inicial ({YEAR_ACTUAL})</p><p style='font-size:24px; color:#28a745; font-weight:bold; margin-top:0px;'>${renta_hoy:,.0f}</p>", unsafe_allow_html=True)
m2.markdown(f"<p style='font-size:16px; margin-bottom:0px;'>🔴 Renta Mensual Proyectada ({año_final})</p><p style='font-size:24px; color:#ff4b4b; font-weight:bold; margin-top:0px;'>${renta_actualizada:,.0f}</p>", unsafe_allow_html=True)
