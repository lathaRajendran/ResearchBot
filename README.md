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
├── eval_runner.py    # LLM-as-judge evaluation suite for agent response quality
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

### Unit Tests
Run the unit tests to verify the conversational routing and graph logic:
```bash
python3 -m unittest test_agent.py
```

### LLM-as-Judge Evaluation
Run the automated LLM evaluation suite to grade the quality, structure, and accuracy of agent responses against predefined rubrics:
```bash
python3 eval_runner.py
```

---

## Observability with OpenTelemetry & Jaeger

The project is instrumented with standard **OpenTelemetry** guidelines for logs, traces, and metrics.

### 1. Traces & Spans
* **Waterfall Timings**: The entire conversational cycle is traced. Spans measure execution durations for individual LangGraph nodes (`generate_query`, `route_search`, `search_web`, `synthesize_report`, `respond_directly`).
* **Trace Metadata**: Spans capture run-time attributes (e.g. `latest_message`, `generated_query`, `search_results_count`, `report_length`).

### 2. Structured Logs
Logger outputs are formatted to automatically inject active `TraceID` and `SpanID` contexts. This enables instant correlation between system logs and trace waterfalls:
```text
2026-07-14 18:30:31,414 [INFO] [TraceID: 15f30a01e9847de20c3fa272f6b44a6e SpanID: faa3cccd60bf592f] research-bot - run_research: Invoked research flow...
```

### 3. System Metrics
Exposes key system performance statistics to the console/collector:
* `research_queries_total`: Count of queries processed.
* `web_searches_total`: Count of Tavily web searches performed.
* `query_processing_duration_seconds`: Histogram distribution of execution latency.

---

## Visualizing Traces in Jaeger

To run a graphical UI dashboard of the agent's waterfall execution graphs:

### 1. Deploy Jaeger via Docker
Start the Jaeger all-in-one container configured to receive OTLP HTTP traffic:
```bash
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

### 2. Update Environment Configuration
In your `.env` file, toggle Jaeger OTLP exporting on:
```env
JAEGER_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces
```

### 3. Search and Analyze
1. Go to **[http://localhost:16686](http://localhost:16686)**.
2. Select **`research-bot`** in the **Service** dropdown menu.
3. Click **Find Traces** to explore timing breakdowns.

---

## LLM-as-Judge Evaluation

The evaluation suite (`eval_runner.py`) uses an independent LLM judge (`gemini-2.5-flash`) to automate quality verification.

### How it Works
1. **Eval Cases**: Runs the agent against a curated set of test inputs containing expected response guidelines (rubrics).
2. **Evaluator Persona**: The judge is instructed to grade the output based on three dimensions:
   - **Accuracy**: Is it factually correct and in line with expectations?
   - **Structure**: Does it follow formatting guidelines?
   - **Relevance**: Does it directly address the query?
3. **Structured Verdicts**: The judge outputs grades (1–5) and a written critique in structured JSON format:
   ```json
   {
     "accuracy_score": 5,
     "structure_score": 5,
     "relevance_score": 5,
     "reasoning": "The response perfectly aligns with the rubric..."
   }
   ```

