import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración y Estilo
st.set_page_config(page_title="Serge Financial Strategy v2.1", layout="wide")
st.title("🏡 Dashboard: Estrategia de Compra (Sweet Spot 4Y)")

YEAR_ACTUAL = datetime.now().year
MESES_NOMBRES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# 2. Sidebar - Inputs
with st.sidebar:
    st.header("⚙️ Fase de Acumulación")
    cap_inicial = st.number_input("Capital Inicial ($)", value=135000, step=5000)
    ahorro_mensual = st.number_input("Aporte Mensual ($)", value=2000, step=100)
    rendimiento_anual = st.number_input("Rendimiento Mercado (%)", value=10.0, step=0.5) / 100
    
    st.header("🎯 Meta de Retiro")
    liquidez_deseada = st.number_input("Liquidez deseada después de la compra ($)", value=120000, step=5000)
    
    st.header("💸 Fase de Desembolso")
    retiro_buffer_hoy = st.number_input("Monto del gasto bianual (valor 2026 $)", value=45000, step=5000)
    inflacion_gastos = st.number_input("Inflación de gastos (%)", value=3.0, step=0.5) / 100
    años_vida_inversiones = st.slider("Cantidad de años para vivir de inversiones", 10, 60, 48)

    st.header("🛡️ Plan de Contingencia")
    años_extra_trabajo = st.slider("Años extra de trabajo post-compra", 0, 20, 13)
    inversion_extra_post = st.number_input("Inversión mensual extra post-compra ($)", value=500, step=100)

# 3. Motor de Cálculo
meses = (4 + años_extra_trabajo + años_vida_inversiones) * 12
datos = []
capital_actual = cap_inicial
apto_comprado = False
año_compra = YEAR_ACTUAL + 4
mes_meta_lograda = ""
año_meta_lograda = None
gasto_buffer_ajustado = retiro_buffer_hoy
inyectado_mensual = ahorro_mensual
retiro_bianual_log = 0
meses_post_retiro = 0

for mes in range(1, meses + 1):
    año_iter = YEAR_ACTUAL + (mes // 12)
    gasto_buffer_ajustado *= (1 + (inflacion_gastos / 12))
    
    # Lógica de Compra (Año 4)
    if mes == 48:
        precio_apto = 200000 * (1.03**4) # Asumiendo 3% inflacion propiedad
        capital_actual -= precio_apto
        apto_comprado = True
        
    # Fase de acumulación post-compra (Trabajo ligero)
    if 48 < mes <= (48 + (años_extra_trabajo * 12)):
        capital_actual += inversion_extra_post
        inyectado_anual_val = inversion_extra_post * 12
    else:
        inyectado_anual_val = 0

    # Lógica de alcanzar la Meta de Liquidez
    if not año_meta_lograda and capital_actual >= liquidez_deseada and mes > 48:
        año_meta_lograda = año_iter
        mes_meta_lograda = MESES_NOMBRES[(mes % 12) - 1]

    # Fase de Retiro (Libertad total)
    if mes > (48 + (años_extra_trabajo * 12)):
        meses_post_retiro += 1
        if meses_post_retiro % 24 == 1:
            capital_actual -= gasto_buffer_ajustado
            retiro_bianual_log = gasto_buffer_ajustado
            
    capital_actual += capital_actual * (rendimiento_anual / 12)

    if mes % 12 == 0:
        datos.append({
            "Año": año_iter,
            "Capital ($)": round(capital_actual),
            "Precio Apt": "COMPRADO" if apto_comprado else "Ahorrando",
            "Inyectado ($)": round(ahorro_mensual * 12 if mes <= 48 else inyectado_anual_val),
            "Retiro ($)": round(retiro_bianual_log),
            "Status": "Retiro 🌴" if mes > (48 + (años_extra_trabajo * 12)) else "Trabajo 💼"
        })
        retiro_bianual_log = 0

df = pd.DataFrame(datos)

# 4. UI y Visualización
col_table, col_chart = st.columns([1, 1])
with col_table:
    st.subheader("📑 Auditoría de Flujo")
    st.dataframe(df.style.format({"Año": "{:.0f}", "Capital ($)": "{:,.0f}"}), height=450, hide_index=True)

with col_chart:
    st.subheader("📈 Evolución de Capital")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='#3b82f6', width=3)))
    fig.add_hline(y=liquidez_deseada, line_dash="dot", line_color="orange", annotation_text="Meta Liquidez")
    fig.update_layout(template="plotly_dark", height=450)
    st.plotly_chart(fig, use_container_width=True)

# 5. Banners Finales con MES detallado
st.markdown("---")
k1, k2 = st.columns(2)
with k1: st.metric("Capital Final Proyectado", f"${capital_actual:,.0f}")
with k2: 
    if año_meta_lograda:
        st.success(f"🎯 Meta lograda en {mes_meta_lograda} de {año_meta_lograda}")
    else:
        st.error("⚠️ Meta no alcanzada en el periodo")

if año_meta_lograda:
    st.info(f"🚀 **Libertad Financiera:** Apartamento comprado en el año {año_compra}. Retiro total iniciado después de los {años_extra_trabajo} años de trabajo extra.")
