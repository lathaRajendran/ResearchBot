"""
Web Research Agent using LangGraph + Tavily Search.

Searches the web for a given topic, synthesizes findings, and returns
a structured research report.

Usage:
    python agent.py
    python agent.py --query "latest advances in quantum computing"
"""

import argparse
import os
import time
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

# Import OpenTelemetry observability constructs
from observability import tracer, logger, query_counter, query_latency, search_counter

load_dotenv()

class ResearchState(TypedDict):
    messages: Annotated[list, add_messages]
    query: str
    search_results: list[dict]
    report: str


def generate_query(state: ResearchState) -> ResearchState:
    with tracer.start_as_current_span("generate_query") as span:
        logger.info("Node generate_query: Starting standalone query generation.")
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        
        system_prompt = (
            "You are an assistant that analyzes a conversation history and determines if a Google search is needed "
            "to answer the user's latest message.\n\n"
            "If a search is needed, respond ONLY with an optimized, standalone search query (keywords). Do not add any conversational text.\n"
            "If NO search is needed (e.g. the message is a greeting like 'hello', a simple follow-up, or general knowledge "
            "that does not require web search), respond ONLY with the exact string: NO_SEARCH"
        )
        
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm.invoke(messages)
        query = response.content.strip()
        
        span.set_attribute("generated_query", query)
        logger.info(f"Node generate_query: Standalone query output is '{query}'")
        return {"query": query}


def route_search(state: ResearchState) -> str:
    with tracer.start_as_current_span("route_search") as span:
        query = state.get("query", "").strip()
        span.set_attribute("query_string", query)
        
        if query == "NO_SEARCH":
            logger.info("Routing decision: Direct response (No Search needed).")
            return "respond_directly"
        
        logger.info(f"Routing decision: Proceed to Web Search with query '{query}'.")
        return "search"


def respond_directly(state: ResearchState) -> ResearchState:
    with tracer.start_as_current_span("respond_directly") as span:
        logger.info("Node respond_directly: Generating response directly from chat history.")
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
        system_prompt = "You are a helpful, conversational web research assistant. Answer the user's message directly based on the conversation history."
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm.invoke(messages)
        
        span.set_attribute("response_length", len(response.content))
        logger.info("Node respond_directly: Completed direct reply generation.")
        return {"report": response.content, "messages": [response]}


def search_web(state: ResearchState) -> ResearchState:
    with tracer.start_as_current_span("search_web") as span:
        query = state["query"]
        span.set_attribute("search_query", query)
        logger.info(f"Node search_web: Executing search on Tavily for: '{query}'")
        
        # Increment metric counter
        search_counter.add(1)
        
        tool = TavilySearch(max_results=5)
        raw_results = tool.invoke(query)
        if isinstance(raw_results, dict):
            results = raw_results.get("results", [])
        elif isinstance(raw_results, list):
            results = raw_results
        else:
            results = []
            
        span.set_attribute("search_results_count", len(results))
        logger.info(f"Node search_web: Retrieved {len(results)} search results.")
        return {"search_results": results}


def synthesize_report(state: ResearchState) -> ResearchState:
    with tracer.start_as_current_span("synthesize_report") as span:
        logger.info("Node synthesize_report: Preparing synthesized research report.")
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        
        results_text = "\n\n".join(
            f"Source: {r.get('url', 'N/A')}\nTitle: {r.get('title', 'N/A')}\nContent: {r.get('content', '')[:500]}"
            for r in state["search_results"]
        )

        system_prompt = (
            "You are a research analyst. Synthesize the web search results to answer the user's latest query, taking into account the conversation history.\n"
            "Provide a clear, structured report with: Summary, Key Findings (bullet points), and Sources.\n\n"
            f"Search Results:\n{results_text}"
        )

        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm.invoke(messages)
        
        span.set_attribute("report_length", len(response.content))
        logger.info("Node synthesize_report: Report synthesis completed.")
        return {"report": response.content, "messages": [response]}


def build_graph() -> StateGraph:
    graph = StateGraph(ResearchState)
    graph.add_node("generate_query", generate_query)
    graph.add_node("search", search_web)
    graph.add_node("synthesize", synthesize_report)
    graph.add_node("respond_directly", respond_directly)
    
    graph.set_entry_point("generate_query")
    
    graph.add_conditional_edges(
        "generate_query",
        route_search,
        {
            "search": "search",
            "respond_directly": "respond_directly"
        }
    )
    
    graph.add_edge("search", "synthesize")
    graph.add_edge("synthesize", END)
    graph.add_edge("respond_directly", END)
    
    return graph.compile()

# -----------------------------
# Build graph once
# -----------------------------
agent = build_graph()

# Public function for Streamlit
# -----------------------------
def run_research(messages: list | str) -> str:
    """
    Execute the research workflow and return the report.
    """
    start_time = time.time()
    
    with tracer.start_as_current_span("run_research") as span:
        logger.info("run_research: Invoked research flow.")
        
        # Increment metric counter
        query_counter.add(1)
        
        formatted_messages = []
        if isinstance(messages, str):
            formatted_messages = [HumanMessage(content=messages)]
        else:
            for msg in messages:
                if isinstance(msg, dict):
                    role = msg.get("role")
                    content = msg.get("content")
                    if role == "user":
                        formatted_messages.append(HumanMessage(content=content))
                    elif role == "assistant":
                        formatted_messages.append(AIMessage(content=content))
                else:
                    formatted_messages.append(msg)

        result = agent.invoke(
            {
                "query": "",
                "messages": formatted_messages,
                "search_results": [],
                "report": "",
            }
        )
        
        duration = time.time() - start_time
        query_latency.record(duration)
        span.set_attribute("execution_duration_seconds", duration)
        
        logger.info(f"run_research: Flow executed successfully in {duration:.3f}s.")
        return result["report"]


def main():
    parser = argparse.ArgumentParser(description="Web Research Agent")
    parser.add_argument("--query", default="latest advances in AI agents 2024", help="Research query")
    args = parser.parse_args()

    print(f"\n🔍 Researching: {args.query}\n")
    result = run_research(args.query)

    print("=" * 60)
    print("📄 RESEARCH REPORT")
    print("=" * 60)
    print(result)


if __name__ == "__main__":
    main()