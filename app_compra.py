import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy_financial as npf
from datetime import datetime

# 1. Configuración de tiempo
YEAR_ACTUAL = 2026 

st.set_page_config(page_title=f"Serge Financial Strategy v4.7.7", layout="wide")

# --- SECCIÓN: HERRAMIENTAS (GASTOS & INTERÉS COMPUESTO) ---
with st.sidebar:
    st.title("🧮 Calculadoras")
    col_calcs_1, col_calcs_2 = st.columns(2)
    
    with col_calcs_1:
        with st.popover("💰 Gastos"):
            tasa_cambio = st.number_input("Tipo de cambio (CRC por USD)", value=460.0, step=1.0)
            moneda_calc = st.radio("Moneda base:", ["USD", "CRC"], horizontal=True)
            step_val = 10.0 if moneda_calc == "USD" else 5000.0
            simbolo = "$" if moneda_calc == "USD" else "₡"
            
            st.divider()
            st.write(f"📊 **Gastos en {moneda_calc}**")
            g_diario = st.number_input(f"Diario/Comida ({simbolo})", value=0.0, step=step_val)
            st.write("**Servicios & HOA**")
            g_luz = st.number_input(f"Luz ({simbolo})", value=0.0, step=step_val)
            g_agua = st.number_input(f"Agua ({simbolo})", value=0.0, step=step_val)
            g_internet = st.number_input(f"Internet ({simbolo})", value=0.0, step=step_val)
            g_cel = st.number_input(f"Celular ({simbolo})", value=0.0, step=step_val)
            g_hoa = st.number_input(f"HOA ({simbolo})", value=0.0, step=step_val)
            g_diversion = st.number_input(f"Diversión ({simbolo})", value=0.0, step=step_val)
            
            total_m = g_diario + g_luz + g_agua + g_internet + g_cel + g_hoa + g_diversion
            total_a = total_m * 12
            
            if moneda_calc == "CRC":
                m_usd = total_m / tasa_cambio
                a_usd = total_a / tasa_cambio
                st.metric("Total Mensual", f"₡{total_m:,.0f}")
                st.caption(f"Equivale a: ${m_usd:,.2f} USD")
                st.caption(f"Total Anual: ₡{total_a:,.0f} / ${a_usd:,.2f} USD")
            else:
                m_crc = total_m * tasa_cambio
                a_crc = total_a * tasa_cambio
                st.metric("Total Mensual", f"${total_m:,.2f}")
                st.caption(f"Equivale a: ₡{m_crc:,.0f} CRC")
                st.caption(f"Total Anual: ${total_a:,.2f} / ₡{a_crc:,.0f} CRC")

    with col_calcs_2:
        with st.popover("📈 Interés"):
            st.write("📊 **Calculadora Compuesta**")
            c_ini = st.number_input("Capital Inicial ($)", value=1000, step=1000)
            a_men = st.number_input("Aporte Mensual ($)", value=500, step=100)
            tasa_int = st.number_input("Rendimiento Anual (%)", value=10.0, step=0.5) / 100
            t_años = st.number_input("Años", value=10, step=1)
            
            datos_int = []
            c_temp = c_ini
            for i in range(1, t_años + 1):
                for _ in range(12):
                    c_temp += a_men
                    c_temp += c_temp * (tasa_int / 12)
                datos_int.append({"Año": i, "Total": round(c_temp)})
            
            st.dataframe(pd.DataFrame(datos_int), hide_index=True, use_container_width=True)
            st.metric("Final", f"${c_temp:,.0f}")

st.title("Dashboard: Libertad Financiera")

MESES_NOMBRES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

if 'año_meta_cache' not in st.session_state:
    st.session_state.año_meta_cache = YEAR_ACTUAL + 5

# 2. Sidebar - Variables principales
with st.sidebar:
    st.header("👤 Perfil")
    edad_actual = st.number_input("Tu edad actual", value=42, step=1)

    st.header("⚙️ Variables de Inversión")
    cap_inicial = st.number_input("Capital Inicial Principal ($)", value=0, step=5000)
    ahorro_mensual = st.number_input("Aporte Mensual Principal ($)", value=2000, step=100)
    rendimiento_anual = st.number_input("Rendimiento del Mercado (%)", value=10.0, step=0.5) / 100
    
    st.header("🏠 Precio Inmueble")
    precio_hoy = st.number_input(f"Precio Maximo Hoy ($)", value=200000, step=5000)
    inflacion_inmueble = st.number_input("Inflación Inmueble (%)", value=4.0, step=0.5) / 100
    
    st.subheader("🏢 Gastos de Condominio")
    cuota_condo_hoy = st.number_input(f"Cuota mensual actual ($)", value=300, step=50)
    inflacion_condo = st.number_input("Incremento anual cuota (%)", value=5.0, step=0.5) / 100

    st.header("🎯 Meta de Retiro")
    liquidez_deseada = st.number_input("Liquidez deseada despues de la compra ($)", value=200000, step=10000)
    
    st.header("💸 Fase de Desembolso")
    retiro_buffer_hoy = st.number_input(f"Monto del gasto bianual hoy {YEAR_ACTUAL} ($)", value=60000, step=5000)
    inflacion_gastos = st.number_input("Inflación de gastos (%)", value=3.0, step=0.5) / 100
    
    años_proyeccion = st.slider("Cantidad de años de proyección total", 10, 80, 60)
    año_final_proy = YEAR_ACTUAL + años_proyeccion
    st.caption(f"Proyección hasta el año: {año_final_proy}")

    st.header("🛡️ Plan de Contingencia")
    año_base = st.session_state.año_meta_cache
    años_extra_trabajo = st.slider(f"Años extra de trabajo post-compra", 0, 20, 1)
    st.caption(f"Fecha estimada de retiro: {año_base + años_extra_trabajo}")
    inversion_extra_mensual = st.number_input("Inversión mensual extra post-compra ($)", value=500, step=100)

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
cuota_condo_ajustada = cuota_condo_hoy
año_agotamiento = None
costo_final_aparta = 0
capital_post_meta = 0
capital_post_laboral = 0 

total_ahorro_propio = cap_inicial
total_intereses_generados = 0
inyectado_anual = 0
retiro_buffer_anual = 0 
condo_anual_acumulado = 0

for mes in range(0, meses):
    año_actual = YEAR_ACTUAL + (mes // 12)
    if not meta_lograda:
        precio_aparta *= (1 + (inflacion_inmueble / 12))
    gasto_buffer_ajustado *= (1 + (inflacion_gastos / 12))
    cuota_condo_ajustada *= (1 + (inflacion_condo / 12))

    if not meta_lograda and capital_actual >= (precio_aparta + liquidez_deseada):
        meta_lograda = True
        año_meta = año_actual
        st.session_state.año_meta_cache = año_meta 
        mes_nombre_meta = MESES_NOMBRES[mes % 12]
        mes_de_la_compra = mes
        costo_final_aparta = precio_aparta
        capital_actual -= precio_aparta
        capital_post_meta = capital_actual
        retiro_buffer_anual += precio_aparta

    if not meta_lograda:
        capital_actual += ahorro_mensual
        inyectado_anual += ahorro_mensual
        total_ahorro_propio += ahorro_mensual
    else:
        capital_actual -= cuota_condo_ajustada
        condo_anual_acumulado += cuota_condo_ajustada
        meses_desde_compra = mes - mes_de_la_compra
        es_periodo_extra = meses_desde_compra <= (años_extra_trabajo * 12)
        if es_periodo_extra:
            capital_actual += inversion_extra_mensual
            inyectado_anual += inversion_extra_mensual
            total_ahorro_propio += inversion_extra_mensual
            if meses_desde_compra == (años_extra_trabajo * 12):
                capital_post_laboral = capital_actual
        else:
            meses_post_trabajo = meses_desde_compra - (años_extra_trabajo * 12)
            if meses_post_trabajo == 1 or (meses_post_trabajo > 1 and meses_post_trabajo % 24 == 0):
                capital_actual -= gasto_buffer_ajustado
                retiro_buffer_anual += gasto_buffer_ajustado
    
    interes_mes = capital_actual * (rendimiento_anual / 12)
    total_intereses_generados += interes_mes
    capital_actual += interes_mes

    if capital_actual <= 0 and año_agotamiento is None:
        año_agotamiento = año_actual

    if (mes + 1) % 12 == 0:
        es_retiro_status = meta_lograda and (mes - mes_de_la_compra > (años_extra_trabajo * 12))
        datos.append({
            "Año": año_actual,
            "Capital ($)": round(capital_actual) if capital_actual > 0 else 0,
            "Precio Apt": "COMPRADO" if meta_lograda and año_actual >= año_meta else f"{round(precio_aparta):,}",
            "Inyectado ($)": round(inyectado_anual),
            "Retiro ($)": round(retiro_buffer_anual),
            "Condo ($)": round(condo_anual_acumulado),
            "Condo_Mes_Graf": round(cuota_condo_ajustada),
            "Gasto_Vida_Graf": round(gasto_buffer_ajustado),
            "Status": "Retiro 🌴" if es_retiro_status else "Activo 💼"
        })
        inyectado_anual = 0; retiro_buffer_anual = 0; condo_anual_acumulado = 0

if años_extra_trabajo == 0:
    capital_post_laboral = capital_post_meta

df = pd.DataFrame(datos)

# 4. Layout
col_table, col_chart = st.columns([1.2, 0.8])
with col_table:
    st.subheader(f"🧬 Proyección a {años_proyeccion} Años")
    libertad_financiera = meta_lograda and año_agotamiento is None
    cols_a_mostrar = ['Año', 'Capital ($)']
    if not libertad_financiera:
        cols_a_mostrar.extend(['Precio Apt', 'Inyectado ($)'])
    if df['Condo ($)'].sum() > 0:
        cols_a_mostrar.append('Condo ($)')
    cols_a_mostrar.extend(['Retiro ($)', 'Status'])
    
    st.dataframe(
        df[cols_a_mostrar].style.format({
            "Año": "{:.0f}", "Capital ($)": "{:,.0f}", 
            "Inyectado ($)": "{:,.0f}", "Retiro ($)": "{:,.0f}", "Condo ($)": "{:,.0f}"
        }), height=400, use_container_width=True, hide_index=True
    )

with col_chart:
    st.subheader("📈 Capital vs Gastos")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Capital ($)'], name="Capital", line=dict(color='#00d1b2', width=3)))
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Condo_Mes_Graf'] * 12, name="Condo Anual", line=dict(color='yellow', dash='dot')))
    fig.add_trace(go.Scatter(x=df['Año'], y=df['Gasto_Vida_Graf'], name="Buffer Vida (2Y)", line=dict(color='orange', dash='dot')))
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=20, b=0), template="plotly_dark", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

# 5. KPIs y Banners
st.markdown("---")
año_libertad = (año_meta if año_meta else YEAR_ACTUAL) + años_extra_trabajo
edad_compra = edad_actual + (año_meta - YEAR_ACTUAL) if año_meta else 0
edad_retiro = edad_actual + (año_libertad - YEAR_ACTUAL)

k1, k2, k3 = st.columns(3)
with k1: st.metric(f"Capital Final ({año_final_proy})", f"${df['Capital ($)'].iloc[-1]:,}")
with k2: st.metric(f"Gasto Bianual Proyectado (Hoy 2026)", f"${retiro_buffer_hoy:,}")
with k3: 
    if meta_lograda: st.success(f"🎯 Aparta comprado en {mes_nombre_meta} {año_meta} (Edad: {edad_compra})")
    else: st.error("🎯 Meta No Alcanzada")

if meta_lograda:
    if año_agotamiento:
        msg_w = f"⚠️ **Alerta de Sistema:** Después de la compra a los **{edad_compra} años** ({mes_nombre_meta} {año_meta}), " + \
                (f"seguidos de {años_extra_trabajo} años de inversión extra. " if inversion_extra_mensual > 0 else f"posponiendo el retiro {años_extra_trabajo} año(s). " if años_extra_trabajo > 0 else "") + \
                f"El capital se agota en **{año_agotamiento}** (Edad: {edad_actual + (año_agotamiento - YEAR_ACTUAL)}), ajusta el plan de contingencia."
        st.warning(msg_w)
    else:
        if años_extra_trabajo > 0:
            if inversion_extra_mensual > 0:
                msg_i = f"🚀 **Libertad Financiera Lograda:** Apartamento comprado a los **{edad_compra} años** ({mes_nombre_meta} de {año_meta}). Se trabajan **{años_extra_trabajo} años adicionales** invirtiendo **${inversion_extra_mensual:,}/mes**, iniciando el retiro a los **{edad_retiro} años** ({mes_nombre_meta} de {año_libertad}). Sostenible hasta el año **{año_final_proy}**."
            else:
                msg_i = f"🚀 **Libertad Financiera Lograda:** Apartamento comprado a los **{edad_compra} años** ({mes_nombre_meta} de {año_meta}). Se **pospone el retiro del buffer por {años_extra_trabajo} año(s)** para permitir crecimiento compuesto, iniciando el retiro a los **{edad_retiro} años** ({mes_nombre_meta} de {año_libertad}). Sostenible hasta el año **{año_final_proy}**."
        else:
            msg_i = f"🚀 **Libertad Financiera Lograda:** Apartamento comprado a los **{edad_compra} años** ({mes_nombre_meta} de {año_meta}). Iniciando el retiro en **{mes_nombre_meta} de {año_meta}**. Sostenible hasta el año **{año_final_proy}**."
        st.info(msg_i)

st.markdown("---")
m1, m2, m3 = st.columns(3)
m1.markdown(f"<p style='font-size:16px; margin-bottom:0px;'>🏠 Costo Final Apartamento</p><p style='font-size:24px; color:#ff4b4b; font-weight:bold; margin-top:0px;'>${costo_final_aparta:,.0f}</p>", unsafe_allow_html=True)
m2.markdown(f"<p style='font-size:16px; margin-bottom:0px;'>💰 Capital Post-Compra</p><p style='font-size:24px; color:#28a745; font-weight:bold; margin-top:0px;'>${capital_post_meta:,.0f}</p>", unsafe_allow_html=True)
m3.markdown(f"<p style='font-size:16px; margin-bottom:0px;'>🏁 Capital Post-Laboral ({año_libertad})</p><p style='font-size:24px; color:#1E90FF; font-weight:bold; margin-top:0px;'>${capital_post_laboral:,.0f}</p>", unsafe_allow_html=True)

# 6. Auditoría
st.markdown("---")
st.markdown("### 📊 Rendimiento del Plan de Inversión")
c1, c2, c3 = st.columns(3)
c1.metric("Total Inyectado", f"${round(total_ahorro_propio):,}")
c2.metric("Intereses Acumulados", f"${round(total_intereses_generados):,}")
c3.metric("Multiplicador", f"{round(total_intereses_generados / total_ahorro_propio, 2)}x")
