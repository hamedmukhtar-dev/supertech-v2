from openai import OpenAI
client = OpenAI()

def ai_insights(prompt):
    response = client.chat.completions.create(
        model="gpt-5.1",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message["content"]

def ai_detect_fraud(activity):
    prompt = f"Analyze this activity for fraud: {activity}"
    return ai_insights(prompt)

def ai_customer_profile(data):
    prompt = f"Generate a customer behavioral profile: {data}"
    return ai_insights(prompt)

def ai_daily_summary(logs):
    prompt = f"Summarize today's system logs: {logs}"
    return ai_insights(prompt)