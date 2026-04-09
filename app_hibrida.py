import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy_financial as npf
from datetime import datetime

# 1. Configuración de tiempo dinámica
YEAR_ACTUAL = datetime.now().year

st.set_page_config(page_title=f"Serge Financial Strategy v3.50", layout="wide")
st.title("🧬 Dashboard de Libertad Financiera (Modelo Híbrido: Cash + Crédito)")

MESES_NOMBRES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# 2. Sidebar
with st.sidebar:
    st.header("⚙️ Acumulación Inicial")
    cap_inicial = st.number_input("Capital Inicial ($)", value=135000, step=5000)
    ahorro_mensual = st.number_input("Aporte Mensual ($)", value=2000, step=100)
    rendimiento_anual = st.number_input("Rendimiento del Mercado (%)", value=10.0, step=0.5) / 100
    
    st.header("🏠 Inmueble y Crédito")
    precio_hoy = st.number_input(f"Precio del aparta (en {YEAR_ACTUAL}) ($)", value=200000, step=5000)
    inflacion_inmueble = st.number_input("Inflación Inmueble (%)", value=4.0, step=0.5) / 100
    
    pct_cash = st.slider("% Pago en Cash (Prima)", 20, 100, 50)
    interes_anual_credito = st.number_input("Tasa de Interés Anual Crédito (%)", value=8.5, step=0.25) / 100
    plazo_años = st.slider("Plazo del Crédito (Años)", 5, 30, 15)
    
    st.header("🎯 Meta de Retiro")
    liquidez_minima_compra = st.number_input("Liquidez mínima para gatillar compra ($)", value=150000, step=10000)
    
    st.header("💸 Fase de Desembolso")
    retiro_buffer_hoy = st.number_input(f"Gasto bianual (valor {YEAR_ACTUAL} $)", value=60000, step=5000)
    inflacion_gastos = st.number_input("Inflación de gastos (%)", value=3.0, step=0.5) / 100
    años_proyeccion = st.slider("Años totales de proyección", 10, 60, 48)

# 3. Motor de Cálculo
meses = años_proyeccion * 12
datos = []
capital_actual = cap_inicial
precio_aparta = precio_hoy
meta_lograda = False
año_meta = None
mes_nombre_meta = ""
mes_de_la_compra = -1
cuota_mensual = 0
meses_restantes_credito = 0
gasto_buffer_ajustado = retiro_buffer_hoy 
año_agotamiento = None
costo_final_aparta = 0
capital_post_meta = 0
inyectado_anual = 0
retiro_anual = 0

# Fila Génesis
datos.append({
    "Año": YEAR_ACTUAL, "Capital ($)": round(cap_inicial), "Status": "Inicio 🚀",
    "Inyectado ($)": 0, "Retiro ($)": 0, "Cuota Crédito ($)": 0
})

for mes in range(1, meses + 1):
    año_actual = YEAR_ACTUAL + (mes // 12)
    nombre_mes_actual = MESES_NOMBRES[(mes % 12) - 1]
    
    if not meta_lograda:
        precio_aparta *= (1 + (inflacion_inmueble / 12))
    
    gasto_buffer_ajustado *= (1 + (inflacion_gastos / 12))

    # Lógica de Compra
    # Se gatilla cuando el capital actual >= Prima Cash + Liquidez Mínima deseada
    prima_necesaria = precio_aparta * (pct_cash / 100)
    monto_credito = precio_aparta - prima_necesaria

    if not meta_lograda and capital_actual >= (prima_necesaria + liquidez_minima_compra):
        meta_lograda = True
        año_meta = año_actual
        mes_nombre_meta = nombre_mes_actual
        mes_de_la_compra = mes
        costo_final_aparta = precio_aparta
        
        # Calculamos la cuota nivelada (amortización francesa)
        if monto_credito > 0:
            cuota_mensual = abs(npf.pmt(interes_anual_credito/12, plazo_años*12, monto_credito))
            meses_restantes_credito = plazo_años * 12
        
        capital_actual -= prima_necesaria
        capital_post_meta = capital_actual
        retiro_anual += prima_necesaria

    # Flujo Mensual
    if not meta_lograda:
        capital_actual += ahorro_mensual
        inyectado_anual += ahorro_mensual
    else:
        # Si hay crédito, pagamos la cuota
        if meses_restantes_credito > 0:
            capital_actual -= cuota_mensual
            meses_restantes_credito -= 1
        
        # Retiro bianual para vivir (inicia 24 meses después de la compra)
        meses_desde_compra = mes - mes_de_la_compra
        if meses_desde_compra > 0 and meses_desde_compra % 24 == 0:
            capital_actual -= gasto_buffer_ajustado
            retiro_anual += gasto_buffer_ajustado

    # Rendimiento
    capital_actual += capital_actual * (rendimiento_anual / 12)

    if capital_actual <= 0 and año_agotamiento is None:
        año_agotamiento = año_actual

    if mes % 12 == 0:
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital_actual) if capital_actual > 0 else 0,
            "Inyectado ($)": round(inyectado_anual),
            "Retiro ($)": round(retiro_anual),
            "Cuota Crédito ($)": round(cuota_mensual) if meses_restantes_credito > 0 else 0,
            "Status": "Viviendo 🏠" if meta_lograda else "Acumulando 💼"
        })
        inyectado_anual = 0; retiro_anual = 0

df = pd.DataFrame(datos)

# 4. Layout
col_table, col_chart = st.columns([1.2, 0.8])
with col_table:
    st.subheader("📑 Flujo de Caja Mixto")
    st.dataframe(df.style.format({
        "Año": "{:.0f}", "Capital ($)": "{:,.0f}", 
        "Inyectado ($)": "{:,.0f}", "Retiro ($)": "{:,.0f}", "Cuota Crédito ($)": "{:,.0f}"
    }), height=400, use_container_width=True, hide_index=True)

with col_chart:
    st.subheader("📈 Proyección de Capital")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='#00d1b2', width=3)))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=20, b=0), template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# 5. KPIs
st.markdown("---")
if meta_lograda:
    k1, k2, k3 = st.columns(3)
    with k1: st.metric("Costo Proyectado Apto", f"${costo_final_aparta:,.0f}")
    with k2: st.metric("Cuota Mensual Crédito", f"${cuota_mensual:,.2f}")
    with k3: st.success(f"🎯 Compra: {mes_nombre_meta} {año_meta}")
    
    st.info(f"💡 Al financiar el {(100-pct_cash)}%, mantuviste una liquidez inicial de **${capital_post_meta:,.0f}** al momento de comprar.")
else:
    st.error("La meta no se alcanza con los parámetros actuales.")

