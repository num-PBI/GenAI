import streamlit as st
from lida import Manager, TextGenerationConfig, llm
from lida.datamodel import Goal
import os
import pandas as pd
from PIL import Image
import io
import base64

df = None
os.makedirs("data", exist_ok=True)

st.set_page_config(page_title="CSV-Plotter", page_icon="📊")

st.write("# CSV-Plotter📊")
st.sidebar.write("## Setup")

# Instructions for Hugging Face API key
st.sidebar.markdown(
    "### Hugging Face Authentication\n"
    "Ensure you have a Hugging Face API key. "
    "Set it as an environment variable or input it below:"
)

# Get Hugging Face API key
hf_api_key = os.getenv("HUGGINGFACE_API_KEY")

if not hf_api_key:
    hf_api_key = st.sidebar.text_input("Enter Hugging Face API key:", type="password")

if not hf_api_key:
    st.error("Please provide your Hugging Face API key to proceed.")
    st.stop()

st.markdown(
    """
    CSV-Plotter is a web app developed on the LIDA library, designed for generating data visualizations and infographics. 
    Learn more on [LIDA's project page](https://microsoft.github.io/lida/).
    """
)

# File upload and summarization
selected_dataset = None
use_cache = st.sidebar.checkbox("Use cache", value=True)

st.sidebar.markdown("### Data Summarization")
file = st.sidebar.file_uploader("Upload your CSV file", type=["csv"])

if file is not None:
    df = pd.read_csv(file)
    summarization_methods = ["llm", "columns", "default"]
    selected_method = st.sidebar.selectbox("Choose a summarization method", options=summarization_methods, index=0)

# Generate data summary
if df is not None and selected_method:
    # Initialize LIDA Manager with Hugging Face model
    text_gen = llm(
        provider="hf",
        model="uukuguy/speechless-llama2-hermes-orca-platypus-13b",
        api_key=hf_api_key,
        device_map="auto"
    )
    lida = Manager(text_gen=text_gen)

    textgen_config = TextGenerationConfig(
        n=1,
        temperature=0,
        model="gpt-3.5-turbo-16k",
        use_cache=use_cache
    )

    st.write("## Summary")
    summary = lida.summarize(df, summary_method=selected_method, textgen_config=textgen_config)

    if "dataset_description" in summary:
        st.write(summary["dataset_description"])

    if "fields" in summary:
        nfields_df = pd.DataFrame([
            {"column": field["column"], **field["properties"]}
            for field in summary.get("fields", [])
        ])
        st.write(nfields_df)
    else:
        st.write(str(summary))

    # Goal generation
    if summary:
        st.sidebar.write("### Goal Selection")
        num_goals = st.sidebar.slider("Number of goals to generate", min_value=1, max_value=10, value=4)
        own_goal = st.sidebar.checkbox("Add Your Own Goal")

        goals = lida.goals(summary, n=num_goals, textgen_config=textgen_config)
        goal_questions = [goal.question for goal in goals]

        if own_goal:
            user_goal = st.sidebar.text_input("Describe Your Goal")
            if user_goal:
                new_goal = Goal(question=user_goal, visualization=user_goal, rationale="")
                goals.append(new_goal)
                goal_questions.append(new_goal.question)

        selected_goal = st.selectbox("Choose a generated goal", options=goal_questions, index=0)
        selected_goal_object = goals[goal_questions.index(selected_goal)]

        # Visualization
        if selected_goal_object:
            st.sidebar.write("## Visualization Library")
            visualization_libraries = ["seaborn", "matplotlib", "plotly"]
            selected_library = st.sidebar.selectbox("Choose a visualization library", options=visualization_libraries, index=0)

            st.write("## Visualization")
            visualizations = lida.visualize(
                summary=summary,
                goal=selected_goal_object,
                textgen_config=textgen_config,
                library=selected_library
            )

            if visualizations:
                viz = visualizations[0]
                img = Image.open(io.BytesIO(base64.b64decode(viz.raster)))
                st.image(img, caption="Visualization Plot", use_column_width=True)

                st.write("### Explanation")
                explanations = lida.explain(code=viz.code, library=selected_library, textgen_config=textgen_config)
                for explanation in explanations[0]:
                    st.markdown(f"**{explanation['section']}**\n{explanation['explanation']}")

                st.write("## Code")
                st.code(viz.code, language="python")
            else:
                st.error("No visualizations available for the selected goal.")
