import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

# Load variables from .env file into os.environ
load_dotenv()

# Set LANGCHAIN environment variables (optional - only if API key is available)
langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
if langsmith_api_key:
    os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    os.environ["LANGCHAIN_PROJECT"] = "ai_idea_to_reality_poc_gpt_4o_testing"

# Set GROQ (optional - only if API key is available)
groq_api_key = os.getenv("GROQ_API_KEY")
if groq_api_key:
    os.environ["GROQ_API_KEY"] = groq_api_key

# GPT-4o Azure setup
gpt_4o_api_key = os.getenv("GPT_4O_API_KEY")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

# Use AzureChatOpenAI for better compatibility with current LangChain version
# Only create the LLM if API key and endpoint are available
if gpt_4o_api_key and azure_endpoint:
    # Fix the endpoint - remove the deployment and API version from the endpoint
    base_endpoint = azure_endpoint.split("/openai/deployments/")[0]
    llm = AzureChatOpenAI(
        model="gpt-4o",
        api_key=gpt_4o_api_key,
        azure_endpoint=base_endpoint,
        azure_deployment="gpt-4o",
        api_version="2025-01-01-preview",
        temperature=0
    )
    print("✅ Azure OpenAI configured successfully")
else:
    # Fallback to a basic LLM or None if Azure OpenAI is not configured
    print("⚠️ Azure OpenAI not configured - using fallback")
    llm = None

memory = MemorySaver()
