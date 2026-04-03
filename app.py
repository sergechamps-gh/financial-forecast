import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración
st.set_page_config(page_title="Serge Financial Forecast v2.1", layout="wide")
st.title("🛡️ Dashboard de Libertad Financiera: Data-First Edition")

# 2. Sidebar con granularidad específica
with st.sidebar:
    st.header("⚙️ Variables")
    cap_inicial = st.number_input("Capital Inicial ($)", value=135000, step=5000)
    ahorro_mensual = st.number_input("Aporte Mensual ($)", value=2000, step=100)
    rendimiento_anual = st.number_input("Rendimiento Mercado (%)", value=8, step=1) / 100
    
    st.header("🏠 Inmueble")
    precio_hoy = st.number_input("Precio Aparta Hoy ($)", value=200000, step=5000)
    inflacion_inmueble = st.number_input("Inflación Inmueble (%)", value=5, step=1) / 100
    
    # Horizonte mínimo de 4 años
    años_proyeccion = st.slider("Horizonte (Años)", 4, 25, 12)

# 3. Motor de Cálculo
meses = años_proyeccion * 12
datos = []
capital = cap_inicial
precio_aparta = precio_hoy
intereses_acumulados = 0

for mes in range(meses + 1):
    año_actual = 2026 + (mes // 12)
    interes_mes = capital * (rendimiento_anual / 12)
    intereses_acumulados += interes_mes
    capital = capital + interes_mes + (ahorro_mensual if mes > 0 else 0)
    precio_aparta = precio_aparta * (1 + inflacion_inmueble / 12)
    
    if mes % 12 == 0:
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital),
            "Precio Apt ($)": round(precio_aparta),
            "Neto ($)": round(capital - precio_aparta),
            "Intereses ($)": round(intereses_acumulados),
            "Inflación ($)": round(precio_aparta - precio_hoy)
        })

df = pd.DataFrame(datos)

# 4. Layout: Priorizando Raw Numbers
col_nums, col_graf = st.columns([1.1, 0.9])

with col_nums:
    st.subheader("📑 Raw Numbers (Corte Anual)")
    # Ajustamos altura para que se vea completo sin scroll
    st.dataframe(
        df.style.format("{:,.0f}"), 
        height=(len(df) + 1) * 35 + 38, 
        use_container_width=True
    )

with col_graf:
    st.subheader("📈 Proyección Visual")
    fig = go.Figure()
    eje_x = df['Año']
    fig.add_trace(go.Scatter(x=eje_x, y=df['Capital ($)'], name="Capital", line=dict(color='royalblue', width=3)))
    fig.add_trace(go.Scatter(x=eje_x, y=df['Precio Apt ($)'], name="Precio Apt", line=dict(color='firebrick', dash='dot')))
    fig.add_trace(go.Scatter(x=eje_x, y=df['Neto ($)'], name="Neto", fill='tozeroy', line=dict(color='green')))
    
    fig.update_layout(height=450, margin=dict(l=0, r=0, t=20, b=0), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# 5. KPIs Finales
st.markdown("---")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Intereses Totales Ganados", f"${intereses_acumulados:,.0f}")
with kpi2:
    st.metric("Costo Extra por Esperar", f"${df.iloc[-1]['Inflación ($)']:,.0f}", delta_color="inverse")
with kpi3:
    meta_check = df[df['Neto ($)'] >= 500000].first_valid_index()
    if meta_check is not None:
        st.success(f"🎯 Meta: Año {df.loc[meta_check, 'Año']}")
    else:
        st.error("🎯 Meta: No alcanzada")
with kpi4:
    st.metric("Inyección de tu bolsillo", f"${(ahorro_mensual * meses):,.0f}")
