from dotenv import load_dotenv
import os
import streamlit as st
import json
import pandas as pd
import openai
import matplotlib.pyplot as plt


openai.api_key = st.secrets["OPENAI_API_KEY"]

client = openai.OpenAI()

st.set_page_config(page_title="Phil Cancler", layout="wide")

if "asked_first_question" not in st.session_state:
    st.session_state["asked_first_question"] = False

st.title("Ask Phil Cancler")
st.markdown("Upload Tableau data and ask questions to Phil Cancler")

uploaded_file = st.file_uploader("Upload your data source", type=["csv", "xlsx", "txt", "json"])

df = None

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith(".txt"):
        df = pd.read_csv(uploaded_file, delimiter="\t")
    elif uploaded_file.name.endswith("json"):
        raw_json = json.load(uploaded_file)
        if isinstance(raw_json, list):
            df = pd.json_normalize(raw_json)
        elif isinstance(raw_json, dict):
            df = pd.json_normalize([raw_json])
        else:
            st.error("Unsupported JSON structure")

    else:
        st.error("Unsupported file format")

    if df is not None:
        st.dataframe(df.head(9), use_container_width=True)

        question = st.text_input("Ask a question about the data")

        if question:
            table_sample = df.head(100).to_markdown(index = False)

            intro = ""
            first_time = False

            if not st.session_state.asked_first_question:
                intro = """Hey. It's me Phil Cancler. What up. I see you have this data file that you dont really "Phil" like analyzing. Heh. No worries, I, Phil Cancler, will analyze the data for you. Now let's see here.\n\n"""
                st.session_state.asked_first_question = True
                first_time = True

            prompt = f"""{intro}You are a business analyst. Here's a data preview:

    {table_sample}

    Question: {question}

    Please provide a helpful, data-driven answer using trends or summaries you observe. Here are a few rules to follow:
    1. If possible, always make sure to determine clusters in you answer.
    2. You have narcissistic personality disorder. Do not say you have it and rarely showcase this in your response.
    3. Every insight you make should end with "Bing!" 
    4. Do not include an introductory line. Begin with the trends or summaries observed.
    """

            with st.spinner("Phil is Analyzing..."):
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert data analyst."},
                        {"role": "user", "content": prompt}
                    ]
                )

            st.markdown("### Insight from Phil Cancler")

            if first_time:
                st.write(intro)

            st.write(response.choices[0].message.content)

            if "graph" in question.lower() or "chart" in question.lower() or "trend" in question.lower():
                x_col = None
                y_col = None

                for col in df.columns:
                    if "year" in col.lower() or "date" in col.lower():
                        x_col = col
                    elif df[col].dtype in ["float64", "int64"] and col != x_col:
                        y_col = col

                if x_col and y_col:
                    fig, ax = plt.subplots()
                    df_sorted = df.sort_values(x_col)
                    ax.plot(df_sorted[x_col], df_sorted[y_col], marker = "o")
                    ax.set_xlabel(x_col)
                    ax.set_ylabel(y_col)
                    st.pyplot(fig)
                else:
                    st.warning("Could not auto-detect X and Y columns for a graph.")

else:
    st.info("Upload your data source to begin")