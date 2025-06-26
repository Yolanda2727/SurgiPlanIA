
import streamlit as st
import pandas as pd
import plotly.express as px
import openai
import time
from datetime import datetime

st.set_page_config(page_title="SurgiPlanIA® Ético", layout="wide")
st.title("🧠 SurgiPlanIA® Ético")
st.subheader("Sistema Ético de Programación Quirúrgica con Validación de Principios Bioéticos")

# Cargar archivo
archivo = st.sidebar.file_uploader("📂 Cargar archivo Excel", type=["xlsx"])
coordinador = st.text_input("👨‍⚕️ Coordinador quirúrgico:")

if archivo:
    df = pd.read_excel(archivo)
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Hora_inicio"] = pd.to_datetime(df["Hora_inicio"], format="%H:%M").dt.time
    df["Dia"] = df["Fecha"].dt.day_name()

    st.subheader("📋 Vista previa de datos")
    st.dataframe(df.head())

    # Alerta ética 1: No maleficencia - solapamiento de personal
    st.subheader("⚠️ Alertas éticas detectadas")
    alertas = []
    for i, r1 in df.iterrows():
        for j, r2 in df.iterrows():
            if i >= j:
                continue
            if r1["Fecha"] == r2["Fecha"] and r1["Hora_inicio"] == r2["Hora_inicio"]:
                if r1["Instrumentador"] == r2["Instrumentador"]:
                    alertas.append(f"Solapamiento de instrumentador: {r1['Instrumentador']} en ID {r1['ID']} y {r2['ID']}")
                if r1["Cirujano"] == r2["Cirujano"]:
                    alertas.append(f"Solapamiento de cirujano: {r1['Cirujano']} en ID {r1['ID']} y {r2['ID']}")

    # Alerta ética 2: Oportunidad - urgencias mal ubicadas
    urgencias_fuera = df[(df["Prioridad"].str.lower() == "urgente") & (~df["Dia"].isin(["Saturday", "Sunday"]))]
    for _, row in urgencias_fuera.iterrows():
        alertas.append(f"Urgencia mal programada en día hábil: Paciente {row['Paciente']} ({row['Fecha']})")

    # Alerta ética 3: Justicia - sobrecarga en quirófano
    sobrecarga_q = df["Quirófano"].value_counts()
    for q, count in sobrecarga_q.items():
        if count > 3:
            alertas.append(f"Quirófano {q} tiene más de 3 procedimientos asignados")

    # Mostrar alertas
    if alertas:
        for a in alertas:
            st.error(a)
    else:
        st.success("✅ No se detectaron trasgresiones éticas en la programación.")

    # Gráfico de resumen de asignación
    st.subheader("📊 Distribución por quirófano")
    fig = px.histogram(df, x="Quirófano", color="Especialidad", title="Asignación por quirófano")
    st.plotly_chart(fig)

    st.subheader("📊 Distribución por días de la semana")
    fig2 = px.histogram(df, x="Dia", color="Prioridad", title="Cirugías programadas por día")
    st.plotly_chart(fig2)

    # Asistente contextual con resumen
    st.subheader("🤖 Asistente Ético-Quirúrgico")
    pregunta = st.text_input("¿Qué deseas consultar?")
    resumen_tabla = df.describe(include='all').fillna("").to_string()

    openai.api_key = st.secrets["OPENAI_API_KEY"]
    assistant_id = "asst_QCQbYElu2uChGd8g4zTlmair"

    if "thread_id" not in st.session_state:
        thread = openai.beta.threads.create()
        st.session_state.thread_id = thread.id

    if pregunta:
        with st.spinner("Consultando al asistente..."):
            contexto = f"Resumen de programación:\n{resumen_tabla}\n\nCoordinador: {coordinador}\n\nPregunta: {pregunta}"
            openai.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=contexto
            )
            run = openai.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id=assistant_id
            )
            while True:
                status = openai.beta.threads.runs.retrieve(thread_id=st.session_state.thread_id, run_id=run.id)
                if status.status == "completed":
                    break
                time.sleep(1)
            messages = openai.beta.threads.messages.list(thread_id=st.session_state.thread_id)
            respuesta = messages.data[0].content[0].text.value
            st.success(respuesta)
else:
    st.info("Por favor cargue un archivo Excel con columnas como: ID, Paciente, Procedimiento, Especialidad, Duración_horas, Fecha, Hora_inicio, Quirófano, Prioridad, Cirujano, Instrumentador.")
