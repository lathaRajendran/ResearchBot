import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from agent import run_research

# Load environment variables
load_dotenv()

# 1. Define evaluation cases
EVAL_DATASET = [
    {
        "query": "Who won the men's singles at Wimbledon 2024?",
        "expected_rubric": "Should name Carlos Alcaraz as the winner. The response should also mention Novak Djokovic as the runner-up and cite sources."
    },
    {
        "query": "Hi there! I am testing your conversational interface.",
        "expected_rubric": "No web search should be performed. The response should be conversational, welcoming, and acknowledge the user is testing the system."
    },
    {
        "query": "What are the latest advances in nuclear fusion energy as of 2024/2025?",
        "expected_rubric": "Should perform web search, synthesize recent advances, output Key Findings and Sources, and contain relevant URLs."
    }
]

# 2. Define the LLM Judge Prompt
JUDGE_SYSTEM_PROMPT = """
You are an expert AI quality evaluator. Your job is to grade the performance of a Web Research Agent.
You will be given:
1. The user's query.
2. The agent's generated response.
3. The expected rubric/criteria.

Evaluate the agent's response on three dimensions (score each 1-5, where 1 is poor and 5 is excellent):
- **Accuracy**: Is the information factually correct and in alignment with the rubric?
- **Structure**: Does it follow the requested output structure (Summary, Key Findings, Sources) where applicable?
- **Relevance**: Does it directly answer the user's intent?

Provide your output in valid JSON format:
{
  "accuracy_score": <1-5>,
  "structure_score": <1-5>,
  "relevance_score": <1-5>,
  "reasoning": "<brief explanation of your grading decisions>"
}
"""

def grade_response(query: str, response: str, rubric: str) -> str:
    """
    Grades the agent response using an independent instance of the LLM.
    """
    judge_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    messages = [
        SystemMessage(content=JUDGE_SYSTEM_PROMPT),
        HumanMessage(content=f"Query: {query}\n\nAgent Response:\n{response}\n\nRubric: {rubric}")
    ]
    judge_result = judge_llm.invoke(messages)
    return judge_result.content

def run_evaluation():
    """
    Runs the agent over the evaluation dataset and prints the LLM-as-judge scores.
    """
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY is not set in environment variables.")
        return

    print("🚀 Starting LLM-as-Judge Evaluation Run...\n")
    
    for i, case in enumerate(EVAL_DATASET):
        print(f"==================================================")
        print(f"CASE {i+1}: {case['query']}")
        print(f"==================================================")
        
        # 1. Run agent query
        print("🤖 Running agent...")
        response = run_research(case['query'])
        print(f"\n--- Agent Response ---\n{response}\n")
        
        # 2. Grade agent response
        print("⚖️ Grading response using LLM-as-judge...")
        grade_json = grade_response(case['query'], response, case['expected_rubric'])
        print(f"\n--- Judge Verdict ---\n{grade_json}\n")

if __name__ == "__main__":
    run_evaluation()
