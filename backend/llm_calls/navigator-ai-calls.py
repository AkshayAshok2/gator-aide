import openai
import json
client = openai.OpenAI(
    #IT IS POSSIBLE YOU WILL NEED TO EDIT THIS API KEY WITH YOUR OWN KEY THAT YOU HAVE GENERATED IF IT DOES NOT WORK
    api_key="sk-NTvLObYUhpI02YV0wNWNGQ",
    base_url="https://api.ai.it.ufl.edu/v1" # LiteLLM Proxy is OpenAI compatible, Read More: https://docs.litellm.ai/docs/proxy/user_keys
)

response = client.chat.completions.create(
    model="llama-3.1-70b-instruct", # model to send to the proxy
    messages = [
        {
            "role": "user",
            "content": "this is a test request, write a short poem"
        }
    ]
)
poem = response.choices[0].message.content
print(poem)
