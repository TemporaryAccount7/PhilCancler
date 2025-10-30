from dotenv import load_dotenv
import os
import streamlit as st
import json
import pandas as pd
import openai
import matplotlib.pyplot as plt
import io
import chardet
from PIL import Image
import base64


openai.api_key = st.secrets["OPENAI_API_KEY"]
client = openai.OpenAI()

st.set_page_config(page_title="Phil Cancler", layout="wide")

if "asked_first_question" not in st.session_state:
    st.session_state["asked_first_question"] = False

st.title("Ask Phil Cancler")
st.markdown("Upload data and ask questions to Phil Cancler")

uploaded_file = st.file_uploader("Upload your data source", type=["csv", "xlsx", "txt", "json"])

df = None

if uploaded_file:
    
    if uploaded_file.name.endswith(".csv"):
        raw_data = uploaded_file.read()
        result = chardet.detect(raw_data)
        detected_encoding = result["encoding"]
        uploaded_file.seek(0)

        try:
            df = pd.read_csv(uploaded_file, encoding=detected_encoding or "utf-8", on_bad_lines="skip")
        except Exception:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding="latin1", on_bad_lines="skip")

    
    elif uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)

    
    elif uploaded_file.name.endswith(".txt"):
        raw_data = uploaded_file.read()
        result = chardet.detect(raw_data)
        detected_encoding = result["encoding"]
        uploaded_file.seek(0)

        try:
            df = pd.read_csv(uploaded_file, delimiter="\t", encoding=detected_encoding or "utf-8", on_bad_lines="skip")
        except Exception:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, delimiter="\t", encoding="latin1", on_bad_lines="skip")

    
    elif uploaded_file.name.endswith(".json"):
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

        df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r'[^a-z0-9]+', '_', regex=True)
    )

        st.dataframe(df.head(9), use_container_width=True)

        with st.form("question_form"):
            question = st.text_input("Ask a question about the data")
            submitted = st.form_submit_button("Ask")

        if submitted:
            table_sample = df.head(500).to_markdown(index=False)
            intro = ""
            first_time = False

            if not st.session_state.asked_first_question:
                intro = """Hey. It's me Phil Cancler. What up. I see you have this data file that you dont really "Phil" like analyzing. Heh. No worries, I, Phil Cancler, will analyze the data for you. Now let's see here.\n\n"""
                st.session_state.asked_first_question = True
                first_time = True

            prompt = f"""{intro}You are a business and data analyst. Here's a data preview:

{table_sample}

Question: {question}

Please provide a helpful, data-driven answer using trends or summaries you observe. 
Rules:
1. You have narcissistic personality disorder. Do not say you have it and showcase this only a tiny bit in your response.
2. Every insight should end with "Bing!"
3. Do not include an introductory line.
4. If the user asks for a graph OR if a graph would help illustrate the insight, you MUST output EXACTLY one line at the end of your response in this format ONLY:
   GRAPH: [chart_type], X=[column_name], Y=[column_name]
5. The GRAPH line MUST use the normalized column names exactly as shown in the data preview above.
6. Do NOT describe the graph. Do NOT add extra punctuation or words on the GRAPH line.
7. If no graph is relevant, write: GRAPH: none
8. When choosing the GRAPH type, Use 'line' for trends over time or sequence, Use 'bar' for category comparisons, Use 'scatter' for numeric-to-numeric relationships, and use 'hist' for distribution of a single numeric column

"""

            with st.spinner("Phil is Analyzing..."):
                response = client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {"role": "system", "content": "You are an expert data analyst."},
                        {"role": "user", "content": prompt}
                    ]
                )

            answer = response.choices[0].message.content
            st.session_state.last_answer = answer
            
            if "last_answer" in st.session_state:
                answer = st.session_state.last_answer
                st.markdown("### Insight from Phil Cancler")

            if first_time:
                st.write(intro)

            st.write(answer.split("GRAPH:")[0].strip())

            lines = answer.split("\n")
            graph_info = None
            for line in lines:
                if line.strip().startswith("GRAPH:"):
                    graph_info = line.strip().replace("GRAPH:", "").strip()
                    lines.remove(line)
                    break

            st.write("\n".join(lines))

            
            if graph_info and graph_info.lower() != "none":
                try:
                    graph_info = graph_info.replace("[", "").replace("]", "").strip()
                    parts = [x.strip() for x in graph_info.split(",")]
                    chart_type = parts[0].lower()

                    if "scatter" in chart_type:
                        chart_type = "scatter"
                    elif "line" in chart_type:
                        chart_type = "line"
                    elif "bar" in chart_type:
                        chart_type = "bar"
                    elif "hist" in chart_type:
                        chart_type = "hist"
                    else:
                        chart_type = "unknown"

                    x_col = parts[1].split("=")[1].strip()
                    y_col = parts[2].split("=")[1].strip()

                    def find_col(name):
                        for c in df.columns:
                            if c.strip().lower() == name.strip().lower():
                                return c
                        return None

                    x_col_real = find_col(x_col)
                    y_col_real = find_col(y_col)

                    if x_col_real and y_col_real:
                        st.divider()
                        st.subheader("Visualization of Data")


                        fig, ax = plt.subplots()
                        if chart_type == "bar":
                            ax.bar(df[x_col_real], df[y_col_real])
                        elif chart_type == "line":
                            ax.plot(df[x_col_real], df[y_col_real])
                        elif chart_type == "scatter":
                            ax.scatter(df[x_col_real], df[y_col_real])
                        elif chart_type == "hist":
                            ax.hist(df[x_col_real], bins=20)
                        else:
                            raise ValueError("Unsupported chart type")

                        ax.set_xlabel(x_col_real)
                        ax.set_ylabel(y_col_real)
                        ax.set_title(f"{chart_type.title()} of {y_col_real} vs {x_col_real}")
                        #st.pyplot(fig)

                        buf = io.BytesIO()
                        fig.savefig(buf, format="png", bbox_inches="tight")
                        buf.seek(0)

                        img = Image.open(buf)
                        st.image(img, width=750, use_container_width=False)

                        st.download_button(
                            label="Download Graph",
                            data=buf,
                            file_name=f"{chart_type}_{y_col_real}_vs_{x_col_real}.png",
                            mime="image/png"
                        )

                    else:
                        st.info("Phil suggested a graph, but the specified columns don't exist. Oops. Bing!")
                except Exception as e:
                    st.info(f"Phil wanted a graph, but it couldn't be generated. Oops. Bing!")
        
            else:
                st.info("Upload your data source to begin")

