import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy_financial as npf
from datetime import datetime

# 1. Configuración dinámica
YEAR_ACTUAL = datetime.now().year

st.set_page_config(page_title="Serge Financial Strategy v3.80", layout="wide")
st.title("🧬 Auditoría de Compra: Costo Real Patrimonial")

MESES_NOMBRES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# 2. Sidebar
with st.sidebar:
    st.header("⚙️ Acumulación Inicial")
    cap_inicial = st.number_input("Capital Inicial ($)", value=135000, step=5000)
    ahorro_mensual = st.number_input("Aporte Mensual ($)", value=2000, step=100)
    rendimiento_anual = st.number_input("Rendimiento Mercado (%)", value=10.0, step=0.5) / 100
    
    st.header("🏠 Inmueble y Préstamo")
    precio_hoy = st.number_input(f"Precio del aparta ({YEAR_ACTUAL}) ($)", value=200000, step=5000)
    inflacion_inmueble = st.number_input("Inflación Inmueble Anual (%)", value=4.0, step=0.5) / 100
    
    pct_cash = st.slider("% Pago en Cash (Prima)", 20, 100, 40, step=5)
    interes_banco = st.number_input("Tasa Interés Banco Anual (%)", value=12.0, step=0.25) / 100
    plazo_años = st.slider("Plazo del Crédito (Años)", 5, 30, 15)
    
    st.header("🛡️ Plan de Contingencia")
    liquidez_minima = st.number_input("Liquidez mínima post-compra ($)", value=200000, step=10000)
    años_extra_trabajo = st.slider("Años extra de trabajo post-compra", 0, 15, 0)
    inversion_extra_mensual = st.number_input("Inversión mensual extra en esos años ($)", value=500, step=100)
    
    st.header("💸 Gastos de Vida")
    retiro_buffer_hoy = st.number_input(f"Gasto bianual (valor {YEAR_ACTUAL} $)", value=45000, step=5000)
    inflacion_gastos = st.number_input("Inflación de Gastos (%)", value=3.0, step=0.5) / 100
    años_proyeccion = st.slider("Años de horizonte financiero", 10, 80, 60)

# 3. Motor de Cálculo
meses = años_proyeccion * 12
datos = []
capital_actual = cap_inicial
precio_aparta = precio_hoy
meta_lograda = False
año_meta = None; mes_nombre_meta = ""
mes_de_la_compra = -1
año_libertad = None; mes_nombre_libertad = ""
año_agotamiento = None
cuota_mensual = 0
meses_restantes_credito = 0
meses_extra_trabajo_pendientes = años_extra_trabajo * 12
gasto_buffer_ajustado = retiro_buffer_hoy
costo_final_aparta = 0
total_intereses_pagados = 0
capital_post_compra = 0
inyectado_anual = 0
retiro_anual = 0
monto_prestamo_final = 0
prima_pagada_final = 0

for mes in range(1, meses + 1):
    año_actual = YEAR_ACTUAL + (mes // 12)
    nombre_mes = MESES_NOMBRES[(mes % 12) - 1]
    
    if not meta_lograda:
        precio_aparta *= (1 + (inflacion_inmueble / 12))
    gasto_buffer_ajustado *= (1 + (inflacion_gastos / 12))

    # Gatillo de Compra
    prima_requerida = precio_aparta * (pct_cash / 100)
    if not meta_lograda and capital_actual >= (prima_requerida + liquidez_minima):
        meta_lograda = True
        año_meta = año_actual
        mes_nombre_meta = nombre_mes
        mes_de_la_compra = mes
        costo_final_aparta = precio_aparta
        prima_pagada_final = prima_requerida
        monto_prestamo_final = precio_aparta - prima_requerida
        
        if monto_prestamo_final > 0:
            cuota_mensual = abs(npf.pmt(interes_banco/12, plazo_años*12, monto_prestamo_final))
            meses_restantes_credito = plazo_años * 12
            total_intereses_pagados = (cuota_mensual * meses_restantes_credito) - monto_prestamo_final
        
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
        
        if meses_extra_trabajo_pendientes > 0:
            capital_actual += inversion_extra_mensual
            inyectado_anual += inversion_extra_mensual
            meses_extra_trabajo_pendientes -= 1
            if meses_extra_trabajo_pendientes == 0:
                año_libertad = año_actual
                mes_nombre_libertad = nombre_mes
        elif años_extra_trabajo == 0 and mes_de_la_compra == mes:
             año_libertad = año_actual
             mes_nombre_libertad = nombre_mes
        else:
            meses_desde_libertad = mes - mes_de_la_compra - (años_extra_trabajo * 12)
            if meses_desde_libertad > 0 and meses_desde_libertad % 24 == 0:
                capital_actual -= gasto_buffer_ajustado
                retiro_anual += gasto_buffer_ajustado

    capital_actual += capital_actual * (rendimiento_anual / 12)
    if capital_actual <= 0 and año_agotamiento is None:
        año_agotamiento = año_actual

    if mes % 12 == 0:
        if not meta_lograda: status = "Acumulando 💼"
        elif meses_extra_trabajo_pendientes > 0: status = "Contingencia 🛡️"
        elif meses_restantes_credito > 0: status = "Pagando Crédito 🏠"
        else: status = "Libertad Total 🌴"

        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital_actual) if capital_actual > 0 else 0,
            "Inyectado ($)": round(inyectado_anual),
            "Retiro/Prima ($)": round(retiro_anual),
            "Cuota Mensual ($)": round(cuota_mensual) if meses_restantes_credito > 0 or (meta_lograda and meses_restantes_credito == plazo_años*12) else 0,
            "Status": status
        })
        inyectado_anual = 0 ; retiro_anual = 0

df = pd.DataFrame(datos)

# 4. Layout
col_table, col_chart = st.columns([1.2, 0.8])
with col_table:
    st.subheader("📑 Auditoría de Flujo")
    st.dataframe(df.style.format({
        "Año": "{:.0f}", "Capital ($)": "{:,.0f}", 
        "Inyectado ($)": "{:,.0f}", "Retiro/Prima ($)": "{:,.0f}", "Cuota Mensual ($)": "{:,.0f}"
    }), height=500, use_container_width=True, hide_index=True)

with col_chart:
    st.subheader("📈 Trayectoria de Capital")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='#00d1b2', width=3)))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, use_container_width=True)

# 5. Resumen Financiero Corregido
st.markdown("---")
if meta_lograda:
    # La matemática de Serge: Costo Total = Prima + Crédito + Intereses
    costo_real_patrimonial = prima_pagada_final + monto_prestamo_final + total_intereses_pagados
    
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Valor Inmueble (Inflado)", f"${round(costo_final_aparta):,}")
    k2.metric("Monto Financiado", f"${round(monto_prestamo_final):,}")
    k3.metric("Intereses Totales", f"${round(total_intereses_pagados):,}", delta="Costo Deuda", delta_color="inverse")
    k4.metric("Costo Total Real", f"${round(costo_real_patrimonial):,}")
    k5.metric("Prima Pagada (Cash)", f"${round(prima_pagada_final):,}")

    if año_agotamiento:
        st.error(f"⚠️ **Alerta:** Compra en {mes_nombre_meta} {año_meta}, pero el capital se agota en {año_agotamiento}.")
    else:
        st.success(f"🚀 **Libertad Lograda:** Compra realizada en **{mes_nombre_meta} {año_meta}**. Libertad financiera iniciada en **{mes_nombre_libertad} {año_libertad}**.")
else:
    st.error("❌ No se alcanza el capital para la prima con los parámetros actuales.")
