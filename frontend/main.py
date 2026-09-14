import os
from openai import OpenAI

# It's best practice to set your API key as an environment variable:
# os.environ["OPENAI_API_KEY"] = "your-api-key-here"
# If the environment variable is set, the client will automatically pick it up.
client = OpenAI(
    api_key="", # Alternatively, pass it directly (not recommended for production)
)

def generate_text(prompt):
    try:
        # Create a chat completion request
        response = client.chat.completions.create(
            model="gpt-4", # You can use "gpt-4", "gpt-4o", etc.
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150, # Optional: limit the length of the response
            temperature=0.7 # Optional: control randomness (0 = deterministic, 1 = creative)
        )
        
        # Extract and return the generated text
        return response.choices[0].message.content
        
    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == "__main__":
    user_prompt = "Tell me a short joke about programming."
    print(f"Prompt: {user_prompt}\n")
    
    result = generate_text(user_prompt)
    print("Response:")
    print(result)