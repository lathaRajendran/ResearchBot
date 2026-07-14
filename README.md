# Web Research Chatbot

An intelligent, stateful web research chatbot powered by **LangGraph**, **Tavily Search**, and **Google Gemini** (`gemini-2.5-flash`). It remembers conversation context and automatically determines whether a query requires live web search or can be answered directly using conversational context.

## Features

- **Conversational Memory**: Remembers past turns, allowing users to ask follow-up questions naturally.
- **Smart Query Generator**: Automatically parses the chat history to generate optimized search keywords or skip web search for simple greetings/questions.
- **Stateful LangGraph Workflow**: Incorporates conditional routing between direct chat response generation and live web research synthesis.
- **Streamlit Interface**: Interactive chat-like UI for real-time conversation and report markdown rendering.
- **Automated Tests**: Unit tests mocking LLM outputs and web search results to ensure workflow robustness.

---

## Project Structure

```text
├── agent.py          # LangGraph implementation, query generator, search & synthesis logic
├── app.py            # Streamlit frontend with stateful chat UI
├── test_agent.py     # Unit test cases for verifying conversational routing
├── requirements.txt  # Project Python dependencies
└── .env              # Environment secrets configuration (API keys)
```

---

## Setup Instructions

### 1. Prerequisites
Make sure you have Python 3.10+ installed.

### 2. Install Dependencies
Install all required libraries from `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root of the project with your API keys:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

---

## How to Run

### Streamlit Chatbot UI
Launch the interactive web chatbot in your browser:
```bash
streamlit run app.py
```

### CLI Mode (Single-Turn)
Run research straight from your command line:
```bash
python agent.py --query "latest advances in quantum computing"
```

---

## Running Automated Tests

Run the unit tests to verify the conversational routing and graph logic:
```bash
python3 -m unittest test_agent.py
```
