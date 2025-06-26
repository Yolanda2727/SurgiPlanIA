
import streamlit as st
import pandas as pd
import plotly.express as px
import openai
import os
import time

st.set_page_config(page_title="SurgiPlanIA® Ético", layout="wide")

# --- Sidebar de carga ---
st.sidebar.header("📂 Carga de datos")
st.sidebar.markdown("Suba un archivo Excel con la programación quirúrgica\n\n**Formato sugerido:**\n- ID, Paciente, Procedimiento, Especialidad, Duración_horas, Fecha, Hora_inicio, Quirófano, Prioridad, Instrumentador, Auxiliar")

uploaded_file = st.sidebar.file_uploader("Usar archivo Excel", type=["xlsx", "xls"])

# --- Campo del coordinador ---
coordinador = st.text_input("🩺 Ingrese el nombre del Coordinador de Cirugía:")

# --- Lectura del archivo ---
if uploaded_file:
    df = pd.read_excel(uploaded_file)
else:
    df = pd.DataFrame({
        "ID": [1, 2, 3],
        "Paciente": ["Juan Pérez", "Ana Gómez", "Carlos Ruiz"],
        "Procedimiento": ["Ortopedia", "Ginecología", "Cirugía General"],
        "Especialidad": ["Ortopedia", "Ginecología", "Cirugía General"],
        "Duración_horas": [3, 2, 1.5],
        "Fecha": pd.to_datetime(["2025-06-24", "2025-06-25", "2025-06-26"]),
        "Hora_inicio": ["08:00", "10:00", "12:00"],
        "Quirófano": ["Q1", "Q2", "Q1"],
        "Prioridad": ["Alta", "Media", "Baja"],
        "Instrumentador": ["Luis A.", "Marta L.", "Carlos T."],
        "Auxiliar": ["Andrea R.", "Jorge S.", "Nina V."]
    })

# --- Título y resumen ---
st.title("🧠 SurgiPlanIA® Ético")
st.subheader("Sistema Ético de Programación Quirúrgica con Validación de Recursos Humanos")
st.markdown(f"**Creador:** Dr. Anderson Díaz Pérez  \n**Coordinador:** {coordinador}")
st.markdown("### 🎯 Objetivo del Modelo")
st.markdown("Este sistema apoya la programación quirúrgica con criterios éticos como justicia, equidad, oportunidad y no maleficencia, evitando solapamientos y sobrecarga del equipo de salud.")

# --- Resumen automático ---
st.subheader("📊 Resumen del archivo")
st.dataframe(df.head())

# --- Gráfico semanal por quirófano ---
df["Fecha"] = pd.to_datetime(df["Fecha"])
df["Semana"] = df["Fecha"].dt.strftime("Semana %U")
df["Mes"] = df["Fecha"].dt.strftime("%B")

mes_seleccionado = st.selectbox("Seleccione el mes a visualizar", df["Mes"].unique())
df_filtrado = df[df["Mes"] == mes_seleccionado]

fig = px.bar(
    df_filtrado,
    x="Fecha",
    y="Duración_horas",
    color="Especialidad",
    facet_col="Quirófano",
    title="Programación de Cirugías por Semana y Quirófano",
    labels={"Duración_horas": "Duración (hrs)", "Fecha": "Fecha"}
)
st.plotly_chart(fig)

# --- Preparar resumen para IA ---
resumen_tabla = df.describe(include='all').fillna("").to_string()

# --- Asistente quirúrgico ético ---
st.subheader("🤖 Asistente Ético-Quirúrgico Inteligente")
query = st.text_input("¿En qué puedo ayudarte hoy como asistente quirúrgico y ético?")

openai.api_key = st.secrets["OPENAI_API_KEY"]
asistente_id = "asst_QCQbYElu2uChGd8g4zTlmair"

if "thread_id" not in st.session_state:
    thread = openai.beta.threads.create()
    st.session_state.thread_id = thread.id

if query:
    with st.spinner("Consultando al asistente..."):
        mensaje_usuario = f"Datos quirúrgicos resumidos:\n{resumen_tabla}\n\nCoordinador: {coordinador}\n\nConsulta: {query}"

        openai.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=mensaje_usuario
        )

        run = openai.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=asistente_id
        )

        while True:
            status = openai.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id, run_id=run.id
            )
            if status.status == "completed":
                break
            time.sleep(1)

        messages = openai.beta.threads.messages.list(thread_id=st.session_state.thread_id)
        respuesta = messages.data[0].content[0].text.value
        st.success(respuesta)
