import streamlit as st
from agent import run_research

st.set_page_config(page_title="Web Research Agent")

st.title("🌐 Web Research Agent")

query = st.chat_input("Ask me anything...")

if query:
    with st.chat_message("user"):
        st.write(query)

    with st.spinner("Searching the web..."):
        report = run_research(query)

    with st.chat_message("assistant"):
        st.markdown(report)