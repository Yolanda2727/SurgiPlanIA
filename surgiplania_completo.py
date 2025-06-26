
import streamlit as st
import pandas as pd
import openpyxl
import plotly.express as px
import time
import openai
import os

# Configurar la página
st.set_page_config(page_title="SurgiPlanIA® Ético", layout="wide")

# Título
st.title("🧠 SurgiPlanIA® Ético")
st.subheader("Sistema Ético de Programación Quirúrgica con Validación de Recursos Humanos")
st.markdown("**Creador:** Dr. Anderson Díaz Pérez")

# Objetivo
with st.expander("🎯 Objetivo del Modelo"):
    st.write("Este sistema inteligente apoya la programación quirúrgica hospitalaria con criterios éticos como justicia, equidad, oportunidad y no maleficencia, evitando solapamientos y sobrecarga del equipo de salud.")

# --- CARGA DE ARCHIVOS ---
st.sidebar.markdown("📁 **Carga de datos**")
uploaded_file = st.sidebar.file_uploader("Sube un archivo Excel o CSV", type=["xlsx", "xls", "csv"])

# Procesamiento del archivo
if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("📊 Vista previa de los datos")
    st.dataframe(df.head())

    st.subheader("📌 Resumen del archivo cargado")
    st.markdown(f"- **Filas:** {df.shape[0]}")
    st.markdown(f"- **Columnas:** {df.shape[1]}")
    st.markdown("- **Nombres de columnas:** " + ", ".join(df.columns))
    st.markdown("- **Filas duplicadas:** " + str(df.duplicated().sum()))
    st.markdown("- **Valores nulos por columna:**")
    st.dataframe(df.isnull().sum())

# --- ASISTENTE ÉTICO-QUIRÚRGICO ---
st.header("🤖 Asistente Ético-Quirúrgico Inteligente")

# Entrada del usuario
query = st.text_input("¿En qué puedo ayudarte hoy como asistente quirúrgico y ético?")

# Configuración del asistente
openai.api_key = st.secrets["OPENAI_API_KEY"]
assistant_id = "asst_QCQbYElu2uChGd8g4zTlmair"  # Reemplazar con el assistant_id correcto

# Crear thread una vez
if "thread_id" not in st.session_state:
    thread = openai.beta.threads.create()
    st.session_state.thread_id = thread.id

# Procesar consulta del usuario
if query:
    with st.spinner("Consultando al asistente..."):
        openai.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=query
        )
        run = openai.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id
        )
        while True:
            status = openai.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
            if status.status == "completed":
                break
            time.sleep(1)

        messages = openai.beta.threads.messages.list(thread_id=st.session_state.thread_id)
        respuesta = messages.data[0].content[0].text.value
        st.success(respuesta)

# Preguntas sugeridas
with st.expander("💡 Preguntas sugeridas"):
    st.markdown("- ¿Qué cirugías hay esta semana?")
    st.markdown("- ¿Qué recursos humanos están disponibles?")
    st.markdown("- ¿Cuánto tiempo toma una cirugía de ortopedia?")
    st.markdown("- ¿Hay conflictos en la programación?")
    st.markdown("- ¿Quién está asignado para lavado quirúrgico este domingo?")
