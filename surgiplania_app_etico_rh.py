# SurgiPlanIA® Ético - Versión Mejorada con Preguntas Sugeridas y Señales Gráficas de Transgresiones
# Basado en código original surgiplania_app_etico_rh.py
# Dependencias (requirements): streamlit, pandas, plotly, openpyxl, openai>=1.12.0, fpdf, openpyxl

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
    df = pd.read_excel(archivo)
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Hora_inicio"] = pd.to_datetime(df["Hora_inicio"], format="%H:%M").dt.time
    df["Dia"] = df["Fecha"].dt.day_name()

    st.subheader("📋 Vista previa de datos")
    st.dataframe(df.head())

    # Detección de alertas éticas
    alertas = []
    for i, r1 in df.iterrows():
        for j, r2 in df.iterrows():
            if i >= j: continue
            if r1["Fecha"] == r2["Fecha"] and r1["Hora_inicio"] == r2["Hora_inicio"]:
                if r1["Instrumentador"] == r2["Instrumentador"]:
                    alertas.append(f"Solapamiento de instrumentador: {r1['Instrumentador']} en ID {r1['ID']} y {r2['ID']}")
                if r1["Cirujano"] == r2["Cirujano"]:
                    alertas.append(f"Solapamiento de cirujano: {r1['Cirujano']} en ID {r1['ID']} y {r2['ID']}")

    df["Prioridad_lower"] = df["Prioridad"].str.lower()
    urgencias_fuera = df[(df["Prioridad_lower"] == "urgente") & (~df["Dia"].isin(["Saturday", "Sunday"]))]
    for _, row in urgencias_fuera.iterrows():
        alertas.append(f"Urgencia mal programada en día hábil: Paciente {row['Paciente']} ({row['Fecha'].date()})")

    conteo_q = df["Quirófano"].value_counts()
    for q, count in conteo_q.items():
        if count > 3:
            alertas.append(f"Quirófano {q} tiene sobrecarga de {count} procedimientos")

    # Mostrar alertas visibles directamente
    st.subheader("⚠️ Alertas éticas detectadas")
    if alertas:
        for a in alertas:
            st.warning(f"❗ {a}")

        # Exportar a PDF
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
                href_pdf = f'<a href="data:application/pdf;base64,{b64}" download="alertas_éticas.pdf">📄 Descargar reporte PDF</a>'
                st.markdown(href_pdf, unsafe_allow_html=True)

        # Exportar a Excel
        alertas_df = pd.DataFrame({"Alertas": alertas})
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_xlsx:
            alertas_df.to_excel(tmp_xlsx.name, index=False)
            with open(tmp_xlsx.name, "rb") as f:
                b64_excel = base64.b64encode(f.read()).decode()
                href_excel = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}" download="alertas_éticas.xlsx">📊 Descargar reporte Excel</a>'
                st.markdown(href_excel, unsafe_allow_html=True)
    else:
        st.success("✅ No se detectaron trasgresiones éticas.")

    # Gráficos
    df_q = pd.DataFrame({"Quirófano": conteo_q.index, "count": conteo_q.values})
    df_q["flag"] = df_q["count"] > 3
    df_q["color"] = df_q["flag"].map({True: "red", False: "steelblue"})
    fig_q = px.bar(df_q, x="Quirófano", y="count", text="count")
    fig_q.update_traces(marker_color=df_q["color"])
    st.plotly_chart(fig_q)

    df_u = df[df["Prioridad_lower"] == "urgente"].groupby("Dia").size().reset_index(name="urgencias")
    df_u["color"] = df_u["urgencias"].apply(lambda x: "red" if x > 0 else "steelblue")
    fig_u = px.bar(df_u, x="Dia", y="urgencias", text="urgencias")
    fig_u.update_traces(marker_color=df_u["color"])
    st.plotly_chart(fig_u)

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
