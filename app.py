import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración y Estética (Restaurada)
st.set_page_config(page_title="Serge Financial Forecast v3.0", layout="wide")
st.title("🛡️ Dashboard de Libertad Financiera: Smart Retirement Edition")

# 2. Sidebar con granularidad específica
with st.sidebar:
    st.header("⚙️ Variables")
    cap_inicial = st.number_input("Capital Inicial ($)", value=135000, step=5000)
    ahorro_mensual = st.number_input("Aporte Mensual ($)", value=2000, step=100)
    rendimiento_anual = st.number_input("Rendimiento Mercado (%)", value=10, step=1) / 100
    
    st.header("🏠 Inmueble")
    precio_hoy = st.number_input("Precio Aparta Hoy ($)", value=200000, step=5000)
    inflacion_inmueble = st.number_input("Inflación Inmueble (%)", value=4, step=1) / 100
    
    st.header("🎯 Meta de Retiro")
    liquidez_deseada = st.number_input("Liquidez Extra ($)", value=500000, step=10000)
    
    # Horizonte extendido a 40 años como pediste
    años_proyeccion = st.slider("Horizonte (Años)", 4, 40, 20)

# 3. Motor de Cálculo con Lógica de "Cese de Aportes"
meses = años_proyeccion * 12
datos = []
capital = cap_inicial
precio_aparta = precio_hoy
intereses_acumulados = 0
inyeccion_bolsillo = 0
meta_lograda = False
año_meta = None

for mes in range(meses + 1):
    año_actual = 2026 + (mes // 12)
    
    # Regla de Oro: ¿Ya tenemos suficiente para la casa + liquidez líquida?
    # Usamos el precio del aparta ajustado por inflación en ese mes exacto
    if capital >= (precio_aparta + liquidez_deseada) and not meta_lograda:
        meta_lograda = True
        año_meta = año_actual
    
    # Si ya se cumplió la meta, el aporte es 0 (no más salario)
    aporte_este_mes = 0 if meta_lograda else (ahorro_mensual if mes > 0 else 0)
    inyeccion_bolsillo += aporte_este_mes
    
    # Interés compuesto mensual
    interes_mes = capital * (rendimiento_anual / 12)
    intereses_acumulados += interes_mes
    
    capital = capital + interes_mes + aporte_este_mes
    precio_aparta = precio_aparta * (1 + (inflacion_inmueble / 12) if mes > 0 else 1)
    
    # Guardamos el corte anual para la tabla
    if mes % 12 == 0:
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital),
            "Precio Apt ($)": round(precio_aparta),
            "Neto ($)": round(capital - precio_aparta),
            "Intereses ($)": round(intereses_acumulados),
            "Inyectado ($)": round(inyeccion_bolsillo),
            "Status": "Retiro" if meta_lograda else "Activo"
        })

df = pd.DataFrame(datos)

# 4. Layout: Restaurando Raw Numbers vs Proyección
col_nums, col_graf = st.columns([1.1, 0.9])

with col_nums:
    st.subheader("📑 Raw Numbers (Corte Anual)")
    # El estilo de la tabla se mantiene pero ahora indica el Status
    st.dataframe(
        df.style.format({
            "Año": "{:.0f}",
            "Capital ($)": "{:,.0f}",
            "Precio Apt ($)": "{:,.0f}",
            "Neto ($)": "{:,.0f}",
            "Intereses ($)": "{:,.0f}",
            "Inyectado ($)": "{:,.0f}"
        }), 
        height=600, 
        use_container_width=True
    )

with col_graf:
    st.subheader("📈 Proyección Visual")
    fig = go.Figure()
    eje_x = df['Año']
    
    # Capital (Línea Azul)
    fig.add_trace(go.Scatter(x=eje_x, y=df['Capital ($)'], name="Capital Total", 
                             line=dict(color='royalblue', width=3)))
    
    # Precio Inmueble (Línea Roja Punteada)
    fig.add_trace(go.Scatter(x=eje_x, y=df['Precio Apt ($)'], name="Precio Apt (Inflación)", 
                             line=dict(color='firebrick', dash='dot')))
    
    # Neto (Área Verde)
    fig.add_trace(go.Scatter(x=eje_x, y=df['Neto ($)'], name="Neto (Capital - Casa)", 
                             fill='tozeroy', line=dict(color='green')))
    
    fig.update_layout(height=500, margin=dict(l=0, r=0, t=20, b=0), hovermode="x unified", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# 5. KPIs Finales (Restaurados y Mejorados)
st.markdown("---")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric("Intereses Totales Ganados", f"${intereses_acumulados:,.0f}")
with kpi2:
    costo_espera = df.iloc[-1]['Precio Apt ($)'] - precio_hoy
    st.metric("Costo Extra por Esperar", f"${costo_espera:,.0f}", delta_color="inverse")
with kpi3:
    if meta_lograda:
        st.success(f"🎯 Meta: Año {año_meta}")
    else:
        st.error("🎯 Meta: No alcanzada aún")
with kpi4:
    st.metric("Inyección de tu bolsillo", f"${inyeccion_bolsillo:,.0f}")
