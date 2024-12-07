import streamlit as st
from lida import Manager, TextGenerationConfig, llm
from lida.datamodel import Goal
import os
import pandas as pd
from PIL import Image
import io
import base64


df=None
# make data dir if it doesn't exist
os.makedirs("data", exist_ok=True)

st.set_page_config(
    page_title="CSV-Plotter",
    page_icon="📊",
)

st.write("# CSV-Plotter📊")

st.sidebar.write("## Setup")

# Step 1 - Get OpenAI API key
#openai_key = os.getenv("OPENAI_API_KEY")

#if not openai_key:
    #openai_key = st.sidebar.text_input("Enter OpenAI API key:")

st.markdown(
    """
    CSV-Plotter is a webapp developed on LIDA library,
    It is a library for generating data visualizations and data-faithful infographics.Details on the components
    of LIDA are described in the [paper here](https://arxiv.org/abs/2303.02927). See the project page [here](https://microsoft.github.io/lida/) for updates!.
""")

# Step 2 - Select a dataset and summarization method
    # Initialize selected_dataset to None
selected_dataset = None

use_cache = st.sidebar.checkbox("Use cache", value=True)

    # Handle dataset selection and upload
st.sidebar.write("## Data Summarization")
st.sidebar.markdown("Please upload your excel file (the file should have extension .csv).")
file = st.sidebar.file_uploader("select your file",type=["csv"])

if file is not None:
        df=pd.read_csv(file)

        st.sidebar.write("### Choose a summarization method")
        summarization_methods = [
            {"label": "llm",
            "description":
            "Uses the LLM to generate annotate the default summary, adding details such as semantic types for columns and dataset description"},
            {"label": "default",
            "description": "Uses dataset column statistics and column names as the summary"},

            {"label": "columns", "description": "Uses the dataset column names as the summary"}]

    # selected_method = st.sidebar.selectbox("Choose a method", options=summarization_methods)
        selected_method = st.sidebar.selectbox(
            'Choose a method',
            options=['llm','column','default'],
            index=0
        )
# Step 3 - Generate data summary
if df is not None and selected_method is not None:
    #lida = Manager(text_gen=llm("openai", api_key=openai_key))
    text_gen = llm(provider="hf", model="meta-llama/Llama-3.1-8B-Instruct", device_map="auto")
    lida = Manager(text_gen=text_gen)
    

    textgen_config = TextGenerationConfig(
        n=1,
        temperature=0,
        model='gpt-3.5-turbo-16k',
        use_cache=use_cache)

    st.write("## Summary")
    # **** lida.summarize *****
    summary = lida.summarize(
        df,
        summary_method=selected_method,
        textgen_config=textgen_config)

    if "dataset_description" in summary:
        st.write(summary["dataset_description"])

    if "fields" in summary:
        fields = summary["fields"]
        nfields = []
        for field in fields:
            flatted_fields = {}
            flatted_fields["column"] = field["column"]
            # flatted_fields["dtype"] = field["dtype"]
            for row in field["properties"].keys():
                if row != "samples":
                    flatted_fields[row] = field["properties"][row]
                else:
                    flatted_fields[row] = str(field["properties"][row])
            # flatted_fields = {**flatted_fields, **field["properties"]}
            nfields.append(flatted_fields)
        nfields_df = pd.DataFrame(nfields)
        st.write(nfields_df)
    else:
        st.write(str(summary))

    # Step 4 - Generate goals
    if summary:
        st.sidebar.write("### Goal Selection")

        num_goals = st.sidebar.slider(
            "Number of goals to generate",
            min_value=1,
            max_value=10,
            value=4)
        own_goal = st.sidebar.checkbox("Add Your Own Goal")

        # **** lida.goals *****
        goals = lida.goals(summary, n=num_goals, textgen_config=textgen_config)
        st.write(f"## Goals ({len(goals)})")

        default_goal = goals[0].question
        goal_questions = [goal.question for goal in goals]

        if own_goal:
            user_goal = st.sidebar.text_input("Describe Your Goal")

            if user_goal:

                new_goal = Goal(question=user_goal, visualization=user_goal, rationale="")
                goals.append(new_goal)
                goal_questions.append(new_goal.question)

        selected_goal = st.selectbox('Choose a generated goal', options=goal_questions, index=0)

        # st.markdown("### Selected Goal")
        selected_goal_index = goal_questions.index(selected_goal)
        st.write(goals[selected_goal_index])

        selected_goal_object = goals[selected_goal_index]

        # Step 5 - Generate visualizations
        if selected_goal_object:
            st.sidebar.write("## Visualization Library")
            visualization_libraries = ["seaborn", "matplotlib", "plotly"]

            selected_library = st.sidebar.selectbox(
                'Choose a visualization library',
                options=visualization_libraries,
                index=0
            )

            # Update the visualization generation call to use the selected library.
            st.write("## Visualization")
            textgen_config = TextGenerationConfig(
                n=1, temperature=0,
                model='gpt-3.5-turbo-16k',
                use_cache=use_cache)

            # **** lida.visualize *****
            visualizations = lida.visualize(
                summary=summary,
                goal=selected_goal_object,
                textgen_config=textgen_config,
                library=selected_library)
            imgdata = base64.b64decode(visualizations[0].raster)
            img = Image.open(io.BytesIO(imgdata))
            st.image(img, caption="Visualization Plot", use_column_width=True)

            if visualizations:
                selected_viz = visualizations[0]  # Select the first visualization
                selected_viz_title = "Visualization 1"  # Title for display
                        # Generate explanation
                explanations = lida.explain(
                    code=selected_viz.code,
                    library=selected_library,
                    textgen_config=textgen_config
                    )

    # Display the explanation in a readable format
                st.write("### Explanation of the Visualization")
                for row in explanations[0]:
                        st.markdown(f"#### **{row['section']}**")
                        st.markdown(f"{row['explanation']}")
                st.write("## Code Block")
                st.code(selected_viz.code, language='python')
            else:
                st.error("No visualizations available for the selected goal.")
