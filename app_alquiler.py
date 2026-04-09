import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy_financial as npf
from datetime import datetime

# 1. Configuración dinámica
YEAR_ACTUAL = datetime.now().year

st.set_page_config(page_title="Serge Financial Strategy v3.50", layout="wide")
st.title("🧬 Dashboard: Compra Híbrida (Cash + Crédito)")

MESES_NOMBRES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# 2. Sidebar
with st.sidebar:
    st.header("⚙️ Variables de Acumulación")
    cap_inicial = st.number_input("Capital Inicial ($)", value=135000, step=5000)
    ahorro_mensual = st.number_input("Aporte Mensual ($)", value=2000, step=100)
    rendimiento_anual = st.number_input("Rendimiento Mercado (%)", value=10.0, step=0.5) / 100
    
    st.header("🏠 Inmueble y Préstamo")
    precio_hoy = st.number_input(f"Precio del aparta (en {YEAR_ACTUAL}) ($)", value=200000, step=5000)
    inflacion_inmueble = st.number_input("Inflación Inmueble Anual (%)", value=4.0, step=0.5) / 100
    
    pct_cash = st.slider("% Pago en Cash (Prima)", 20, 100, 50)
    interes_banco = st.number_input("Tasa Interés Banco Anual (%)", value=8.5, step=0.25) / 100
    plazo_años = st.slider("Plazo del Crédito (Años)", 5, 30, 15)
    
    st.header("🎯 Objetivo post-compra")
    liquidez_minima = st.number_input("Liquidez mínima libre ($)", value=100000, step=10000)
    
    st.header("💸 Gastos de Vida")
    retiro_buffer_hoy = st.number_input(f"Gasto bianual (valor {YEAR_ACTUAL} $)", value=60000, step=5000)
    inflacion_gastos = st.number_input("Inflación de Gastos (%)", value=3.0, step=0.5) / 100
    
    años_proyeccion = st.slider("Años de horizonte financiero", 10, 60, 48)

# 3. Motor de Cálculo
meses = años_proyeccion * 12
datos = []
capital_actual = cap_inicial
precio_aparta = precio_hoy
meta_lograda = False
año_meta = None ; mes_nombre_meta = ""
año_agotamiento = None
cuota_mensual = 0
meses_restantes_credito = 0
gasto_buffer_ajustado = retiro_buffer_hoy
costo_final_aparta = 0
capital_post_compra = 0
inyectado_anual = 0
retiro_anual = 0

for mes in range(1, meses + 1):
    año_actual = YEAR_ACTUAL + (mes // 12)
    if not meta_lograda:
        precio_aparta *= (1 + (inflacion_inmueble / 12))
    gasto_buffer_ajustado *= (1 + (inflacion_gastos / 12))

    # Lógica de Gatillo
    prima_requerida = precio_aparta * (pct_cash / 100)
    monto_credito = precio_aparta - prima_requerida

    if not meta_lograda and capital_actual >= (prima_requerida + liquidez_minima):
        meta_lograda = True
        año_meta = año_actual
        mes_nombre_meta = MESES_NOMBRES[(mes % 12) - 1]
        costo_final_aparta = precio_aparta
        
        if monto_credito > 0:
            cuota_mensual = abs(npf.pmt(interes_banco/12, plazo_años*12, monto_credito))
            meses_restantes_credito = plazo_años * 12
        
        capital_actual -= prima_requerida
        capital_post_compra = capital_actual
        retiro_anual += prima_requerida

    # Flujo mensual
    if not meta_lograda:
        capital_actual += ahorro_mensual
        inyectado_anual += ahorro_mensual
    else:
        if meses_restantes_credito > 0:
            capital_actual -= cuota_mensual
            meses_restantes_credito -= 1
        
        meses_desde_compra = mes - ((año_meta - YEAR_ACTUAL) * 12)
        if meses_desde_compra > 0 and meses_desde_compra % 24 == 0:
            capital_actual -= gasto_buffer_ajustado
            retiro_anual += gasto_buffer_ajustado
    
    capital_actual += capital_actual * (rendimiento_anual / 12)

    if capital_actual <= 0 and año_agotamiento is None:
        año_agotamiento = año_actual

    if mes % 12 == 0:
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital_actual) if capital_actual > 0 else 0,
            "Inyectado ($)": round(inyectado_anual),
            "Retiro/Prima ($)": round(retiro_anual),
            "Cuota Crédito ($)": round(cuota_mensual) if meses_restantes_credito > 0 else 0,
            "Status": "Libertad 🌴" if meta_lograda else "Acumulando 💼"
        })
        inyectado_anual = 0 ; retiro_anual = 0

df = pd.DataFrame(datos)

# 4. Layout
col_table, col_chart = st.columns([1.2, 0.8])
with col_table:
    st.subheader("📑 Auditoría de Flujo Mixto")
    st.dataframe(df.style.format({
        "Año": "{:.0f}", "Capital ($)": "{:,.0f}", 
        "Inyectado ($)": "{:,.0f}", "Retiro/Prima ($)": "{:,.0f}",
        "Cuota Crédito ($)": "{:,.0f}"
    }), height=500, use_container_width=True, hide_index=True)

with col_chart:
    st.subheader("📈 Proyección de Capital")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='#00d1b2', width=3)))
    fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0, r=0, t=20, b=0), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

# 5. Banners y KPIs
st.markdown("---")
año_final = YEAR_ACTUAL + años_proyeccion

if meta_lograda:
    if año_agotamiento:
        st.warning(f"⚠️ **Alerta:** Compra lograda en {año_meta}, pero el capital se agota en {año_agotamiento}.")
    else:
        st.info(f"🚀 **Libertad Lograda:** Compra en {mes_nombre_meta} {año_meta}. Sostenible hasta el {año_final}.")
else:
    st.error("❌ No se alcanza la liquidez para comprar con los parámetros actuales.")

k1, k2, k3 = st.columns(3)
with k1: st.metric(f"Capital Final ({año_final})", f"${df['Capital ($)'].iloc[-1]:,}")
with k2: st.metric("Cuota Mensual Banco", f"${cuota_mensual:,.2f}")
with k3: 
    if meta_lograda: st.success(f"🎯 Compra: {año_meta}")
    else: st.error("🎯 Meta No Alcanzada")

m1, m2 = st.columns(2)
m1.markdown(f"<p style='font-size:16px; margin-bottom:0px;'>🏠 Costo Propiedad al Comprar</p><p style='font-size:24px; color:#ff4b4b; font-weight:bold; margin-top:0px;'>${costo_final_aparta:,.0f}</p>", unsafe_allow_html=True)
m2.markdown(f"<p style='font-size:16px; margin-bottom:0px;'>💰 Capital Libre post-prima</p><p style='font-size:24px; color:#28a745; font-weight:bold; margin-top:0px;'>${capital_post_compra:,.0f}</p>", unsafe_allow_html=True)
