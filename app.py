import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de Pantalla
st.set_page_config(page_title="Serge Financial Strategy v3.12", layout="wide")
st.title("🛡️ Dashboard de Libertad Financiera: Análisis de Sostenibilidad")

# 2. Sidebar
with st.sidebar:
    st.header("⚙️ Variables")
    cap_inicial = st.number_input("Capital Inicial ($)", value=135000, step=5000)
    ahorro_mensual = st.number_input("Aporte Mensual ($)", value=2000, step=100)
    rendimiento_anual = st.number_input("Rendimiento Mercado (%)", value=10, step=1) / 100
    
    st.header("🏠 Inmueble")
    precio_hoy = st.number_input("Precio Aparta Hoy ($)", value=200000, step=5000)
    inflacion_inmueble = st.number_input("Inflación Inmueble (%)", value=4.0, step=0.5) / 100
    
    st.header("🎯 Meta de Retiro")
    liquidez_deseada = st.number_input("Liquidez Extra Inicial ($)", value=500000, step=10000)
    
    st.header("💸 Fase de Desembolso (Inflada)")
    retiro_buffer_hoy = st.number_input("Gasto 2 años (valor hoy $)", value=60000, step=5000)
    inflacion_gastos = st.number_input("Inflación de Gastos (%)", value=3.0, step=0.5) / 100
    
    años_proyeccion = st.slider("Horizonte (Años)", 4, 40, 20)

# 3. Motor de Cálculo
meses = años_proyeccion * 12
datos = []
capital = cap_inicial
precio_aparta = precio_hoy
intereses_acumulados = 0
meta_lograda = False
año_meta = None
mes_de_la_compra = -1
gasto_buffer_ajustado = retiro_buffer_hoy 

inyectado_anual = 0
interes_anual = 0
retiro_anual = 0

for mes in range(meses + 1):
    año_actual = 2026 + (mes // 12)
    
    # Inflación mensual
    if mes > 0:
        if not meta_lograda:
            precio_aparta *= (1 + (inflacion_inmueble / 12))
        gasto_buffer_ajustado *= (1 + (inflacion_gastos / 12))

    # Evento de Compra
    if not meta_lograda and capital >= (precio_aparta + liquidez_deseada):
        meta_lograda = True
        año_meta = año_actual
        mes_de_la_compra = mes
        gasto_total_inicial = precio_aparta + gasto_buffer_ajustado
        capital -= gasto_total_inicial
        retiro_anual += gasto_total_inicial
    
    # Capitalización vs Retiros
    if not meta_lograda:
        if mes > 0:
            capital += ahorro_mensual
            inyectado_anual += ahorro_mensual
    else:
        meses_desde_compra = mes - mes_de_la_compra
        if meses_desde_compra > 0 and meses_desde_compra % 24 == 0:
            capital -= gasto_buffer_ajustado
            retiro_anual += gasto_buffer_ajustado
    
    # Crecimiento Mercado
    rendimiento_mes = capital * (rendimiento_anual / 12)
    capital += rendimiento_mes
    interes_anual += rendimiento_mes
    intereses_acumulados += rendimiento_mes

    # Registro Anual
    if mes % 12 == 0 and mes > 0:
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital),
            "Precio Apt": "COMPRADO" if meta_lograda else f"{round(precio_aparta):,}",
            "Inyectado ($)": round(inyectado_anual),
            "Intereses ($)": round(interes_anual),
            "Retiro ($)": round(retiro_anual),
            "Gasto_Invisible_2Y": round(gasto_buffer_ajustado), # Lo guardamos para el gráfico
            "Status": "Retiro 🌴" if meta_lograda else "Activo 💼"
        })
        inyectado_anual = 0
        interes_anual = 0
        retiro_anual = 0

df = pd.DataFrame(datos)

# 4. Layout Visual
col_table, col_chart = st.columns([1.2, 0.8])
with col_table:
    st.subheader("📑 Raw Numbers (Corte Anual)")
    # Tabla limpia sin la columna de Gasto
    st.dataframe(df.drop(columns=['Gasto_Invisible_2Y']).style.format({
        "Año": "{:.0f}", "Capital ($)": "{:,.0f}", 
        "Inyectado ($)": "{:,.0f}", "Intereses ($)": "{:,.0f}", "Retiro ($)": "{:,.0f}"
    }), height=550, use_container_width=True)

with col_chart:
    st.subheader("📈 Proyección Visual: Capital vs Gasto Inflado")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital Total", line=dict(color='royalblue', width=3)))
    
    # RESTAURADA: Línea Naranja de Gasto Inflado (Costo Buffer 2Y)
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Gasto_Invisible_2Y'], name="Costo Buffer (2Y)", line=dict(color='orange', dash='dot')))
    
    # Precio Apt (Solo hasta la meta)
    df_apt = df[df['Precio Apt'] != "COMPRADO"]
    if not df_apt.empty:
        precios_v = [float(str(x).replace(',', '')) for x in df_apt['Precio Apt']]
        fig.add_trace(go.Scatter(x=df_apt['Año'], y=precios_v, name="Precio Apt", line=dict(color='firebrick', dash='dot', width=1)))
    
    fig.update_layout(height=450, margin=dict(l=0, r=0, t=20, b=0), template="plotly_dark", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

# 5. KPIs y Análisis Dinámico
st.markdown("---")
k1, k2, k3 = st.columns(3)
with k1: 
    st.metric("Rendimiento Total", f"${intereses_acumulados:,.0f}")
with k2: 
    # FIX: Removido el paréntesis para que se lea completo
    st.metric("Costo Buffer (Vida)", f"${retiro_buffer_hoy:,.0f} / 2 años")
with k3: 
    if meta_lograda:
        st.success(f"🎯 Comprado & Libre en {año_meta}")
    else:
        st.error("🎯 Meta No Alcanzada")

# Bloque de Análisis Inferior
if meta_lograda:
    st.info(f"💡 **Análisis de Sostenibilidad:** En el año {año_meta} compraste la casa y fondeaste tu primer buffer de 2 años (ajustado por inflación). El capital restante sigue trabajando. Revisa el gráfico arriba: si la línea naranja (`Costo Buffer (2Y)`) se une o cruza con la línea azul (`Capital Total`), tu capital se está agotando y tu plan no es sostenible a largo plazo con esas variables.")
