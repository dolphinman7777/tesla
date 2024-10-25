import asyncio
import ollama

def test_ollama():
    try:
        # Check available models
        models = ollama.list()
        print("Available Models:", models)
        
        # Test a simple chat interaction
        prompt = "Hello, Jeff!"
        response = ollama.chat(
            model="phi3.5:latest",
            messages=[
                {"role": "system", "content": "You are Jeff, an AI assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        print("Response:", response)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_ollama()