import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración dinámica
YEAR_ACTUAL = datetime.now().year

st.set_page_config(page_title="Serge Financial Strategy v1.7", layout="wide")
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
    
    st.header("🎯 Meta de Retiro")
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
    else:
        capital_actual -= renta_actualizada
        if (mes % 24 == 0):
            capital_actual -= gasto_buffer_ajustado
    
    capital_actual += capital_actual * (rendimiento_anual / 12)

    if capital_actual <= 0 and año_agotamiento is None:
        año_agotamiento = año_actual

    if mes % 12 == 0:
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital_actual), # MOSTRAR NEGATIVOS
            "Renta Mensual": round(renta_actualizada),
            "Status": "Libertad 🌴" if meta_lograda else "Acumulando 💼"
        })

df = pd.DataFrame(datos)

# 4. Layout
col_table, col_chart = st.columns([1, 1])
with col_table:
    st.subheader(f"📑 Proyección a {años_proyeccion} Años")
    st.dataframe(df.style.format({"Año": "{:.0f}", "Capital ($)": "{:,.0f}"}), use_container_width=True, hide_index=True)

with col_chart:
    st.subheader("📈 Evolución del Capital")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='#00d1b2', width=3)))
    fig.add_hline(y=0, line_dash="dash", line_color="red") # LÍNEA ROJA DE PELIGRO
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# 5. Banners de Sostenibilidad (Lógica Serge v1.7)
st.markdown("---")
año_final = YEAR_ACTUAL + años_proyeccion

if meta_lograda:
    if año_agotamiento:
        st.warning(f"⚠️\n\n**Hito Alcanzado pero Insuficiente:** Se logró la meta de ${liquidez_deseada:,.0f} en **{año_meta}**, pero el capital se agota en el año **{año_agotamiento}**. Para cubrir el horizonte completo, necesitas subir el capital mínimo requerido.")
    else:
        st.info(f"🚀\n\n**Libertad Financiera Lograda:** Meta alcanzada en {mes_nombre_meta} de {año_meta}. El capital es suficiente hasta el año **{año_final}** de forma sostenible.")
else:
    st.error("❌ Meta no alcanzada dentro del horizonte proyectado.")
