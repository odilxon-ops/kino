from openai import OpenAI

client = OpenAI(
    api_key="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"
)

response = client.responses.create(
    model="gpt-4.1-mini",
    input="Salom Sunnatulla"
)

print(response.output[0].content[0].text)