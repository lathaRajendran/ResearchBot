import streamlit as st
from agent import run_research
from observability import tracer, logger

st.set_page_config(page_title="Web Research Agent")

st.title("🌐 Web Research Agent")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask me anything..."):
    # Start a trace span for user message interaction
    with tracer.start_as_current_span("user_chat_interaction") as span:
        span.set_attribute("user_query", prompt)
        logger.info(f"Received user query: {prompt}")

        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Thinking..."):
            # Run research flow passing the conversation history
            response = run_research(st.session_state.messages)

        span.set_attribute("assistant_response_length", len(response))
        logger.info(f"Generated assistant response with length {len(response)}")

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})