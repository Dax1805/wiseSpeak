from transformers import pipeline

summarizer = None

def get_short_answer(text, max_length=30, min_length=10):
    global summarizer
    if summarizer is None:
        summarizer = pipeline("summarization", model="google/pegasus-xsum")

    try:
        result = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        return result[0]["summary_text"]
    except Exception as e:
        return f"Summarization failed: {str(e)}"
