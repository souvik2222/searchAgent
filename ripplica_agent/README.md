# Ripplica Web Query Agent

A smart, AI-powered agent that classifies, searches, summarizes, and stores web queries using browser automation and LLMs.

---

## 🚀 Features

- **Query validation** (valid/invalid, e.g. "walk my pet" is invalid)
- **Query similarity detection** (embeddings, finds similar past queries)
- **Automated web search & scraping** (Playwright, DuckDuckGo/Google fallback)
- **Summarization of top results** (Hugging Face LLMs)
- **Result caching** for similar queries
- **Modern CLI and Web UI** (Flask, Bootstrap, streaming)
- **Recent query history** and instant reload
- **Streaming UI**: See summaries as they are generated, live!

---

## 🏗️ Architecture

```mermaid
flowchart TD
   flowchart TD
    A[User Query] --> B{Query Validator}
    B -- Invalid --> Z[Show Error]
    B -- Valid --> C[Embedding & Similarity Check]
    C -- Similar Found --> D[Return Cached Summary]
    C -- No Similar --> E[Web Search (Playwright)]
    E --> F[Scrape Top 5 Results]
    F --> G[Summarize Each Result (LLM)]
    G --> H[Show Summaries, Save to DB]
    H --> I[Future Similar Queries]
```

---

## 🖥️ Usage

### 1. **Install dependencies**

```bash
pip install -r requirements.txt
playwright install
```

### 2. **Run the CLI**

```bash
python ripplica_agent/main.py ask "Your query here"
```

### 3. **Run the Web UI (Classic)**

```bash
python ripplica_agent/web_ui.py
# Visit http://127.0.0.1:5000/
```

### 4. **Run the Web UI (Streaming, recommended!)**

```bash
python ripplica_agent/web_ui_stream.py
# Visit http://127.0.0.1:5000/
```

---

## 🧠 How it Works

1. **User enters a query** (CLI or web UI)
2. **Query is validated** (rule-based, can be extended to LLM)
3. **Query embedding is generated** and checked for similarity with past queries
4. If a **similar query is found**, the cached summary is returned
5. If not, the agent **searches DuckDuckGo/Google using Playwright**, scrapes the top 5 results, and extracts text & titles
6. The **scraped content is summarized** (Hugging Face LLM)
7. The **summary and embedding are stored** for future similar queries
8. The **summary is displayed** to the user, live (streaming UI)

---

## 🛠️ Extending the Project

- Swap in a more advanced LLM for summarization or validation
- Add user authentication and persistent history
- Add more search engines or advanced scraping
- Deploy to the cloud (Render, Heroku, etc)

---

## 📄 Example Queries

- "Best places to visit in Delhi"
- "Python list comprehensions explained"
- "Top 5 AI tools in 2024"

---

## 📦 Project Structure

```
ripplica_agent/
├── main.py                # CLI entry point
├── query_validator.py     # Query validation logic
├── embeddings.py          # Embedding & similarity logic
├── search_scraper.py      # Playwright web search & scraping
├── summarizer.py          # Summarization logic (Hugging Face)
├── storage.py             # SQLite storage for queries/results
├── web_ui.py              # Classic Flask web UI
├── web_ui_stream.py       # Advanced streaming Flask web UI
├── requirements.txt
└── README.md
```
