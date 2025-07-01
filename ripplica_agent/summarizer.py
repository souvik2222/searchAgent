from typing import List, Tuple
from transformers import pipeline

# Load summarization pipeline (bart-large-cnn is good, fallback to t5-small if needed)
summarizer = pipeline('summarization', model='facebook/bart-large-cnn')

def summarize_texts(results: List[Tuple[str, str, str]], debug: bool = False) -> str:
    """
    Summarizes a list of (url, title, text) tuples into a single summary string using Hugging Face transformers.
    """
    summaries = []
    for url, title, text in results:
        if not text.strip():
            if debug:
                print(f"[DEBUG] No text to summarize for {url}")
            summaries.append(f"- [{title}]({url})\n  No readable content found.\n")
            continue
        chunk = text[:1024]
        try:
            summary = summarizer(chunk, max_length=120, min_length=30, do_sample=False)[0]['summary_text']
            if debug:
                print(f"[DEBUG] Summary for {url}: {summary}")
        except Exception as e:
            summary = f"Error summarizing: {e}"
            if debug:
                print(f"[DEBUG] Error summarizing {url}: {e}")
        # Show a snippet of the summary for each URL
        summaries.append(f"- [{title}]({url})\n  {summary.strip()}\n")
    if not summaries:
        return "No summaries could be generated."
    return '\n'.join(summaries) 