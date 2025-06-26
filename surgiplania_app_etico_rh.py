
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import random
import openai
import time

st.set_page_config(page_title="SurgiPlanIA® Ético", layout="wide")
st.title("🧠 SurgiPlanIA® Ético")
st.subheader("Sistema Ético de Programación Quirúrgica con Validación de Recursos Humanos")
st.markdown("**Creador:** Dr. Anderson Díaz Pérez")
st.markdown("### 🎯 Objetivo del Modelo")
st.markdown("Este sistema inteligente apoya la programación quirúrgica hospitalaria con criterios éticos como justicia, equidad, oportunidad y no maleficencia, evitando solapamientos y sobrecarga del equipo de salud.")
st.markdown("---")

st.sidebar.header("📁 Carga de datos")
if st.sidebar.button("Usar datos de ejemplo"):
    cirugias = pd.DataFrame({
        "ID": [1, 2, 3],
        "Paciente": ["Juan Pérez", "Ana Torres", "Luis Gómez"],
        "Procedimiento": ["Colecistectomía", "Histerectomía", "Artroscopia"],
        "Especialidad": ["Cirugía General", "Ginecología", "Ortopedia"],
        "Duración_horas": [2, 3, 1.5],
        "Fecha": ["2025-06-24", "2025-06-25", "2025-06-26"],
        "Hora_inicio": ["08:00", "10:00", "09:00"],
        "Quirófano": ["Q1", "Q2", "Q1"],
        "Prioridad": ["Alta", "Media", "Urgente"],
        "Paciente_Estrato": [2, 3, 1],
        "Demora_Días": [5, 8, 12],
        "Cirujano": ["Dr. Ruiz", "Dr. Ruiz", "Dra. Gómez"],
        "Instrumentador": ["Lic. Marta", "Lic. Marta", "Lic. Juan"]
    })

    def prioridad_etica(row):
        score = 0
        if row["Prioridad"] == "Urgente":
            score += 3
        if row["Especialidad"] in ["Oncología", "Cardiología"]:
            score += 2
        if row["Paciente_Estrato"] in [1, 2]:
            score += 1
        if row["Demora_Días"] > 10:
            score += 1
        return score

    cirugias["Score_Etico"] = cirugias.apply(prioridad_etica, axis=1)
    cirugias = cirugias.sort_values(by="Score_Etico", ascending=False)
    cirugias['Inicio'] = pd.to_datetime(cirugias['Fecha'] + ' ' + cirugias['Hora_inicio'])
    cirugias['Fin'] = cirugias['Inicio'] + cirugias['Duración_horas'].apply(lambda x: timedelta(hours=x))

    st.header("🔍 Validación de Solapamiento del Personal Quirúrgico")
    alertas = []
    for idx1, row1 in cirugias.iterrows():
        for idx2, row2 in cirugias.iterrows():
            if idx1 >= idx2:
                continue
            if row1["Cirujano"] == row2["Cirujano"] or row1["Instrumentador"] == row2["Instrumentador"]:
                if not (row1["Fin"] <= row2["Inicio"] or row2["Fin"] <= row1["Inicio"]):
                    conflicto = f"⚠️ Conflicto: {row1['Cirujano']} o {row1['Instrumentador']} asignado en {row1['ID']} y {row2['ID']}"
                    alertas.append(conflicto)
    if alertas:
        for a in alertas:
            st.error(a)
    else:
        st.success("✅ No hay solapamientos de personal.")

    st.header("📆 Calendario Quirúrgico Ético")
    fig = px.timeline(cirugias, x_start="Inicio", x_end="Fin", y="Quirófano", color="Especialidad",
                      hover_data=["Paciente", "Procedimiento", "Cirujano", "Instrumentador", "Score_Etico"])
    fig.update_yaxes(categoryorder="category ascending")
    st.plotly_chart(fig, use_container_width=True)

    st.header("📋 Cronograma Completo")
    st.dataframe(cirugias)

    st.header("📤 Exportar Informe")
    with pd.ExcelWriter("programacion_etica_completa.xlsx") as writer:
        cirugias.to_excel(writer, sheet_name="Cronograma", index=False)
    with open("programacion_etica_completa.xlsx", "rb") as file:
        st.download_button(label="📥 Descargar Excel", data=file, file_name="programacion_etica_completa.xlsx")

st.header("🤖 Asistente Ético-Quirúrgico Inteligente")
query = st.text_input("¿En qué puedo ayudarte hoy como asistente quirúrgico y ético?")

openai.api_key = st.secrets["OPENAI_API_KEY"]
asistente_id = "asst_QCQbYElu2uChGd8g4zTlmair"

if "thread_id" not in st.session_state:
    thread = openai.beta.threads.create()
    st.session_state.thread_id = thread.id

if query:
    with st.spinner("Consultando al asistente..."):
        openai.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=query
        )
        run = openai.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=asistente_id
        )
        while True:
            status = openai.beta.threads.runs.retrieve(thread_id=st.session_state.thread_id, run_id=run.id)
            if status.status == "completed":
                break
            time.sleep(1)

        messages = openai.beta.threads.messages.list(thread_id=st.session_state.thread_id)
        respuesta = messages.data[0].content[0].text.value
        st.success(respuesta)

st.markdown("---")
st.markdown("🔒 Sistema Ético Quirúrgico. © 2025 Dr. Anderson Díaz Pérez")
