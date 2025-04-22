from transformers import pipeline

summarizer = pipeline("summarization", model="google/pegasus-xsum")

text = """
Your phone may slow down due to too many open apps, storage issues, or software needing updates. Closing apps and freeing space can improve performance.
"""

summary = summarizer(text, max_length=60, min_length=20, do_sample=False)
print("🧠 Pegasus Summary:", summary[0]['summary_text'])
