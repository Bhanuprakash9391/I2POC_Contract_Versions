#!/usr/bin/env python3
"""
Test script to verify API key configurations and connectivity
"""

import os
import sys
from dotenv import load_dotenv

def test_api_keys():
    """Test all API key configurations"""
    print("🔍 Testing API Key Configurations...")
    
    # Load environment variables
    load_dotenv()
    
    # Test OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    gpt4o_key = os.getenv("GPT_4O_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    print(f"📋 Environment Variables Found:")
    print(f"   OPENAI_API_KEY: {'✅ Found' if openai_key else '❌ Not found'}")
    if openai_key:
        print(f"      Key: {openai_key[:10]}...{openai_key[-10:]}")
    
    print(f"   GPT_4O_API_KEY: {'✅ Found' if gpt4o_key else '❌ Not found'}")
    if gpt4o_key:
        print(f"      Key: {gpt4o_key[:10]}...{gpt4o_key[-10:]}")
    
    print(f"   GROQ_API_KEY: {'✅ Found' if groq_key else '❌ Not found'}")
    if groq_key:
        print(f"      Key: {groq_key[:10]}...{groq_key[-10:]}")
    
    # Test Azure OpenAI configuration
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    print(f"   AZURE_OPENAI_ENDPOINT: {'✅ Found' if azure_endpoint else '❌ Not found'}")
    if azure_endpoint:
        print(f"      Endpoint: {azure_endpoint}")
    
    # Test DeepSeek API key
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    print(f"   DEEPSEEK_API_KEY: {'✅ Found' if deepseek_key else '❌ Not found'}")
    if deepseek_key:
        print(f"      Key: {deepseek_key[:10]}...{deepseek_key[-10:]}")
    
    # Test LangSmith API key
    langsmith_key = os.getenv("LANGSMITH_API_KEY")
    print(f"   LANGSMITH_API_KEY: {'✅ Found' if langsmith_key else '❌ Not found'}")
    if langsmith_key:
        print(f"      Key: {langsmith_key[:10]}...{langsmith_key[-10:]}")
    
    # Test MongoDB configuration
    mongodb_url = os.getenv("MONGODB_URL")
    mongodb_db = os.getenv("MONGODB_DATABASE")
    print(f"   MONGODB_URL: {'✅ Found' if mongodb_url else '❌ Not found'}")
    print(f"   MONGODB_DATABASE: {'✅ Found' if mongodb_db else '❌ Not found'}")
    
    # Test API connectivity
    print("\n🔗 Testing API Connectivity...")
    
    # Test OpenAI API
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            models = client.models.list()
            print("✅ OpenAI API: Connected successfully")
        except Exception as e:
            print(f"❌ OpenAI API: Failed - {e}")
    else:
        print("⚠️ OpenAI API: No API key available")
    
    # Test Azure OpenAI
    if gpt4o_key and azure_endpoint:
        try:
            from openai import AzureOpenAI
            client = AzureOpenAI(
                api_key=gpt4o_key,
                api_version="2025-01-01-preview",
                azure_endpoint=azure_endpoint
            )
            print("✅ Azure OpenAI: Configuration valid")
        except Exception as e:
            print(f"❌ Azure OpenAI: Failed - {e}")
    else:
        print("⚠️ Azure OpenAI: Missing API key or endpoint")
    
    print("\n📊 Summary:")
    available_keys = sum([bool(openai_key), bool(gpt4o_key), bool(groq_key)])
    print(f"   Total API keys available: {available_keys}/3")
    
    if available_keys == 0:
        print("❌ No valid API keys found. Please set at least one API key.")
        print("   Options:")
        print("   - OPENAI_API_KEY: Standard OpenAI API key")
        print("   - GPT_4O_API_KEY: Azure OpenAI API key") 
        print("   - GROQ_API_KEY: Groq API key")
    else:
        print("✅ API keys configured successfully")

if __name__ == "__main__":
    test_api_keys()
