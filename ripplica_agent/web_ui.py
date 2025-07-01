from flask import Flask, render_template_string, request, redirect, url_for
from query_validator import is_valid_query
from embeddings import get_embedding
from storage import get_similar, save_result
from search_scraper import search_and_scrape
from summarizer import summarize_texts

app = Flask(__name__)

# Store recent queries in memory for demo (could use DB for persistence)
RECENT_QUERIES = []

TEMPLATE = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Web Query Agent</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script>
      function copyToClipboard(text) {
        navigator.clipboard.writeText(text);
      }
    </script>
  </head>
  <body class="bg-light">
    <div class="container py-5">
      <h1 class="mb-4">🔎 Web Query Agent</h1>
      <form method="post">
        <div class="mb-3">
          <input type="text" class="form-control" name="query" placeholder="Enter your web search query" value="{{ query|default('') }}" required>
        </div>
        <button type="submit" class="btn btn-primary">Search</button>
      </form>
      {% if error %}
        <div class="alert alert-danger mt-4">{{ error }}</div>
      {% endif %}
      {% if info %}
        <div class="alert alert-info mt-4">{{ info }}</div>
      {% endif %}
      {% if summaries %}
        <div class="mt-4">
          <h4>📄 Summaries</h4>
          {% for s in summaries %}
            <div class="accordion mb-2" id="accordion{{ loop.index }}">
              <div class="accordion-item">
                <h2 class="accordion-header" id="heading{{ loop.index }}">
                  <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse{{ loop.index }}" aria-expanded="false" aria-controls="collapse{{ loop.index }}">
                    <a href="{{ s.url }}" target="_blank">{{ s.title }}</a>
                  </button>
                </h2>
                <div id="collapse{{ loop.index }}" class="accordion-collapse collapse" aria-labelledby="heading{{ loop.index }}" data-bs-parent="#accordion{{ loop.index }}">
                  <div class="accordion-body">
                    <pre style="white-space: pre-wrap;">{{ s.summary }}</pre>
                    <button class="btn btn-outline-secondary btn-sm" onclick="copyToClipboard(`{{ s.summary|replace('`', '\`') }}`)">Copy Summary</button>
                  </div>
                </div>
              </div>
            </div>
          {% endfor %}
        </div>
      {% endif %}
      {% if recent %}
        <div class="mt-5">
          <h5>Recent Queries</h5>
          <ul class="list-group">
            {% for q in recent %}
              <li class="list-group-item d-flex justify-content-between align-items-center">
                <form method="post" action="/">
                  <input type="hidden" name="query" value="{{ q }}">
                  <button type="submit" class="btn btn-link p-0">{{ q }}</button>
                </form>
              </li>
            {% endfor %}
          </ul>
        </div>
      {% endif %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  </body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    query = ''
    error = None
    info = None
    summaries = None
    if request.method == 'POST':
        query = request.form['query']
        if not is_valid_query(query):
            error = "❌ This is not a valid query. Please enter a web search question."
        else:
            embedding = get_embedding(query)
            similar = get_similar(query, embedding)
            if similar:
                q, summary, sim = similar
                info = f"Found similar past query (similarity {sim:.2f}): {q}"
                # Parse summary into cards (assume markdown format)
                summaries = []
                for line in summary.split('\n- ')[1:]:
                    if line.strip():
                        parts = line.strip().split('\n', 1)
                        title_url = parts[0]
                        summ = parts[1] if len(parts) > 1 else ''
                        if title_url.startswith('['):
                            title = title_url.split('](')[0][1:]
                            url = title_url.split('](')[1][:-1]
                        else:
                            title = url = title_url
                        summaries.append({'title': title, 'url': url, 'summary': summ.strip()})
            else:
                info = "Searching the web and summarizing..."
                results = search_and_scrape(query)
                if not results:
                    error = "❌ No web results found. Please try a different query."
                else:
                    summary = summarize_texts(results)
                    if not summary.strip():
                        error = "❌ Summary could not be generated. The web pages may have had little or no readable content."
                    else:
                        # Parse summary into cards
                        summaries = []
                        for url, title, text in results:
                            summ = summarize_texts([(url, title, text)])
                            summaries.append({'title': title, 'url': url, 'summary': summ.replace(f'- [{title}]({url})', '').strip()})
                        save_result(query, embedding, summary)
            # Add to recent queries
            if query not in RECENT_QUERIES:
                RECENT_QUERIES.insert(0, query)
            if len(RECENT_QUERIES) > 10:
                RECENT_QUERIES.pop()
    return render_template_string(TEMPLATE, query=query, error=error, info=info, summaries=summaries, recent=RECENT_QUERIES)

if __name__ == '__main__':
    # Do NOT use debug=True with Playwright; it causes browser process errors on reload.
    app.run(debug=False, threaded=True) 