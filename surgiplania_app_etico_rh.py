
import streamlit as st
import pandas as pd
import plotly.express as px
import openai
import datetime

st.set_page_config(page_title="SurgiPlanIA® Ético", layout="wide")
st.title("🤖 Asistente Ético-Quirúrgico Inteligente")

# Ingreso del coordinador
coordinador = st.text_input("👨‍⚕️ Ingrese el nombre del Coordinador de Cirugía:")

# Carga de archivo
st.sidebar.title("📂 Carga de datos")
file = st.sidebar.file_uploader("Suba un archivo Excel con la programación quirúrgica", type=["xlsx", "xls"])

# API Key segura
openai.api_key = st.secrets["OPENAI_API_KEY"]
asistente_id = "asst_QCQbYElu2uChGd8g4zTlmair"

if file:
    df = pd.read_excel(file)

    st.subheader("📊 Vista previa de los datos cargados")
    st.dataframe(df.head())

    st.subheader("📋 Resumen automático de los datos")
    resumen = {
        "Total de cirugías": len(df),
        "Especialidades únicas": df['Especialidad'].nunique() if 'Especialidad' in df.columns else "No disponible",
        "Quirófanos disponibles": df['Quirófano'].nunique() if 'Quirófano' in df.columns else "No disponible",
        "Días incluidos": df['Fecha'].dt.day_name().unique() if 'Fecha' in df.columns else "No disponible",
        "Promedio duración": f"{df['Duración horas'].mean():.2f} horas" if 'Duración horas' in df.columns else "No disponible"
    }
    for k, v in resumen.items():
        st.write(f"- **{k}:** {v}")

    st.subheader("💡 Preguntas sugeridas")
    preguntas = [
        "¿Qué cirugías están programadas para el sábado?",
        "¿Quién es el instrumentador asignado al lavado quirúrgico del domingo?",
        "¿Cuál es la cirugía más larga?",
        "¿Cuántas urgencias hay esta semana?",
        "¿Qué quirófano tiene mayor carga?"
    ]
    for q in preguntas:
        st.markdown(f"👉 {q}")

    query = st.text_input("🗣️ ¿En qué puedo ayudarte hoy como asistente quirúrgico y ético?")

    if query:
        with st.spinner("Consultando al asistente..."):
            thread = openai.beta.threads.create()
            openai.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"{query}. Aquí está el resumen de los datos cargados: {resumen}"
            )
            run = openai.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=asistente_id
            )
            while True:
                status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                if status.status == "completed":
                    break
            messages = openai.beta.threads.messages.list(thread_id=thread.id)
            respuesta = messages.data[0].content[0].text.value
            st.success(respuesta)

    st.caption("🧑‍⚕️ Sistema Ético Quirúrgico. © 2025 Dr. Anderson Díaz Pérez. Coordinador: " + (coordinador if coordinador else "No ingresado"))
