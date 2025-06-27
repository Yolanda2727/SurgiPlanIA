# SurgiPlanIA® Ético - Versión Mejorada con Preguntas Sugeridas y Señales Gráficas de Transgresiones
# Basado en código original surgiplania_app_etico_rh.py
# Dependencias (requirements): streamlit, pandas, plotly, openpyxl, openai>=1.12.0, fpdf

import streamlit as st
import pandas as pd
import plotly.express as px
import openai
import time
from datetime import datetime
from fpdf import FPDF
import base64
import tempfile

# Configuración de la página
st.set_page_config(page_title="SurgiPlanIA® Ético", layout="wide")
st.title("🧠 SurgiPlanIA® Ético")
st.subheader("Sistema Ético de Programación Quirúrgica con Validación de Principios Bioéticos")

# Subir archivo y datos del coordinador
archivo = st.sidebar.file_uploader("📂 Cargar archivo Excel", type=["xlsx"])
coordinador = st.text_input("👨‍⚕️ Coordinador quirúrgico:")

# Preguntas sugeridas para el coordinador
preguntas_sugeridas = [
    "¿Existen solapamientos de instrumentador?",
    "¿Existen solapamientos de cirujano?",
    "¿Se programaron urgencias en días hábiles?",
    "¿Algún quirófano tiene sobrecarga de más de 3 procedimientos?",
    "¿Cuál es la distribución de cirugías por quirófano?",
    "¿Cuál es la programación de cirugías por día de la semana según prioridad?"
]
pregunta_sugerida = st.selectbox("❓ Preguntas sugeridas", preguntas_sugeridas)
usar_sugerida = st.checkbox("Usar pregunta sugerida")
if usar_sugerida:
    pregunta = pregunta_sugerida
else:
    pregunta = st.text_input("❓ Escribe tu pregunta personalizada")

if archivo:
    # Leer y procesar datos
    df = pd.read_excel(archivo)
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Hora_inicio"] = pd.to_datetime(df["Hora_inicio"], format="%H:%M").dt.time
    df["Dia"] = df["Fecha"].dt.day_name()

    st.subheader("📋 Vista previa de datos")
    st.dataframe(df.head())

    # Detección de alertas éticas
    alertas = []
    # 1. No maleficencia - solapamiento
    for i, r1 in df.iterrows():
        for j, r2 in df.iterrows():
            if i >= j: continue
            if r1["Fecha"] == r2["Fecha"] and r1["Hora_inicio"] == r2["Hora_inicio"]:
                if r1["Instrumentador"] == r2["Instrumentador"]:
                    alertas.append(f"Solapamiento de instrumentador: {r1['Instrumentador']} en ID {r1['ID']} y {r2['ID']}")
                if r1["Cirujano"] == r2["Cirujano"]:
                    alertas.append(f"Solapamiento de cirujano: {r1['Cirujano']} en ID {r1['ID']} y {r2['ID']}")

    # 2. Oportunidad - urgencias en días hábiles
    df["Prioridad_lower"] = df["Prioridad"].str.lower()
    urgencias_fuera = df[(df["Prioridad_lower"] == "urgente") & (~df["Dia"].isin(["Saturday", "Sunday"]))]
    for _, row in urgencias_fuera.iterrows():
        alertas.append(f"Urgencia mal programada en día hábil: Paciente {row['Paciente']} ({row['Fecha'].date()})")

    # 3. Justicia - sobrecarga de quirófano
    conteo_q = df["Quirófano"].value_counts()
    for q, count in conteo_q.items():
        if count > 3:
            alertas.append(f"Quirófano {q} tiene sobrecarga de {count} procedimientos")

    # Mostrar alertas en recuadro visible
    st.subheader("⚠️ Alertas éticas detectadas")
    if alertas:
        with st.expander("🔍 Ver detalles de las alertas", expanded=True):
            for a in alertas:
                st.markdown(f"- ❗ {a}")

        # Exportar alertas a PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "Reporte de Alertas Éticas - SurgiPlanIA

")
        for a in alertas:
            pdf.multi_cell(0, 10, f"- {a}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            pdf.output(tmp_file.name)
            with open(tmp_file.name, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="alertas_éticas.pdf">📄 Descargar reporte PDF de alertas</a>'
                st.markdown(href, unsafe_allow_html=True)

    else:
        st.success("✅ No se detectaron trasgresiones éticas.")

    # Gráfico de distribución por quirófano con señal de sobrecarga
    st.subheader("📊 Asignación por quirófano (rojo: sobrecarga)")
    df_q = pd.DataFrame({"Quirófano": conteo_q.index, "count": conteo_q.values})
    df_q["flag"] = df_q["count"] > 3
    df_q["color"] = df_q["flag"].map({True: "red", False: "steelblue"})
    fig_q = px.bar(df_q, x="Quirófano", y="count", text="count")
    fig_q.update_traces(marker_color=df_q["color"])
    st.plotly_chart(fig_q)

    # Gráfico de urgencias por día con señal
    st.subheader("📊 Urgencias por día (rojo: urgencias en días hábiles)")
    df_u = df[df["Prioridad_lower"] == "urgente"].groupby("Dia").size().reset_index(name="urgencias")
    df_u["color"] = df_u["urgencias"].apply(lambda x: "red" if x > 0 else "steelblue")
    fig_u = px.bar(df_u, x="Dia", y="urgencias", text="urgencias")
    fig_u.update_traces(marker_color=df_u["color"])
    st.plotly_chart(fig_u)

    # Asistente Ético-Quirúrgico Intelligent
    st.subheader("🤖 Asistente Ético-Quirúrgico")
    resumen_tabla = df.describe(include='all').fillna("").to_string()

    openai.api_key = st.secrets["OPENAI_API_KEY"]
    assistant_id = "asst_QCQbYElu2uChGd8g4zTlmair"
    if "thread_id" not in st.session_state:
        thread = openai.beta.threads.create()
        st.session_state.thread_id = thread.id

    if pregunta:
        with st.spinner("Consultando al asistente..."):
            contexto = f"Resumen de programación:\n{resumen_tabla}\n\nCoordinador: {coordinador}\n\nPregunta: {pregunta}"
            openai.beta.threads.messages.create(thread_id=st.session_state.thread_id, role="user", content=contexto)
            run = openai.beta.threads.runs.create(thread_id=st.session_state.thread_id, assistant_id=assistant_id)
            while True:
                status = openai.beta.threads.runs.retrieve(thread_id=st.session_state.thread_id, run_id=run.id)
                if status.status == "completed":
                    break
                time.sleep(1)
            messages = openai.beta.threads.messages.list(thread_id=st.session_state.thread_id)
            respuesta = messages.data[0].content[0].text.value
            st.success(respuesta)
else:
    st.info("Por favor cargue un archivo Excel con columnas obligatorias.")
