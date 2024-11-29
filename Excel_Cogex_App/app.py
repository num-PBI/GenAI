import pandas as pd
import os
import streamlit as st
from openai import AzureOpenAI
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
from datetime import datetime
api_key=st.text_input("Please paste your open AI key here")
if api_key is not None:
  llm = ChatOpenAI(
            openai_api_key =api_key,
            temperature = 0,
            max_tokens = 4000,
            model_name= "gpt-3.5-turbo-16k"
        )

  st.title("Cognizant Excel file chatbot")
  st.write("Please upload your xslx file to ask the question")
  file = st.file_uploader("select your file",type=["xlsx"])

  if file is not None:
    df=pd.read_excel(file)
    df['ProjectEnddate2'] = pd.to_datetime(df['ProjectEnddate'])
    df['Days_Remaining'] = (df['ProjectEnddate2'] - datetime.now()).dt.days
    df['ProjectStartdate1'] = pd.to_datetime(df['ProjectStartdate'])
    df['Days_passed'] = (datetime.now()-df['ProjectStartdate1']).dt.days
    user_question=st.text_input("If you have other questions related to the file please enter here..")
    button2=st.button("Submit Question")
    with st.sidebar:
        st.title("Please select in the drop down if u want to send project specific emails")
        a=st.selectbox('Please select one project type',('MGMNT','EXTN','SALES','PDP','INFRA','TCE','CRPIT','DMGMT','INVMT','CORP','RCMNT','BENCH','EXANT','MKTAL','OPS','CAPEX','UAMCP','ELT','GGMS','PRDCG')),
        b=st.selectbox('Please select from which Project date u want to calculate days',('Project start date','Project end date')),
        c=st.text_input("Please enter the days")
        e=st.selectbox('PLease select the days passed from the date or remaining to the date',('Passed','Remaining')),
        d=st.selectbox('PLease select either u want the results to be equal,greater or less than the amount of days u specify',('Equal to','Greater than','Less than')),
        st.write(f"Your Query will be Sending mails to all manger under project type {a} who has {d} {c} days {e} from {b}. If u wish to continue please press on submit.")
        button = st.button("Submit") 
    input1=f"Give me IDs of all managers in a python list with each item should be iterable, whose Days {e} from {b} is {d} {c} and project type is {a}"
    if button is True:   
        agent=create_pandas_dataframe_agent(llm,df,verbose=False,allow_dangerous_code=True,max_iterations=60)
        result=agent.invoke(input1)
        result = result["output"].rstrip(']').lstrip('[')
        result= result.split(",")
       
        for i in range(0,len(result)):
            result[i] = result[i].lstrip(' ')+'@cognizant.com'
        # st.write()
        st.write(result)
        #st.write("The emails are ready . Do you want to send?")
    if button2 is True:
          agent=create_pandas_dataframe_agent(llm,df,verbose=False,allow_dangerous_code=True,max_iterations=60)
          result=agent.invoke(user_question)
          st.write(result)
 
