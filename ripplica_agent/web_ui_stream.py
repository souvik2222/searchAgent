from flask import Flask, render_template_string, request, Response, stream_with_context
from query_validator import is_valid_query
from embeddings import get_embedding
from storage import get_similar, save_result
from search_scraper import search_and_scrape
from summarizer import summarize_texts
import json

app = Flask(__name__)

TEMPLATE = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Web Query Agent (Streaming)</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      .spinner-border { width: 2rem; height: 2rem; }
      .summary-card { margin-bottom: 1rem; }
    </style>
  </head>
  <body class="bg-light">
    <div class="container py-5">
      <h1 class="mb-4">🔎 Web Query Agent <small class="text-muted">(Streaming)</small></h1>
      <form id="queryForm" autocomplete="off">
        <div class="mb-3">
          <input type="text" class="form-control" id="queryInput" name="query" placeholder="Enter your web search query" required>
        </div>
        <button type="submit" class="btn btn-primary">Search</button>
      </form>
      <div id="progress" class="mt-4"></div>
      <div id="summaries" class="mt-4"></div>
      <div id="error" class="alert alert-danger mt-4 d-none"></div>
    </div>
    <script>
      const form = document.getElementById('queryForm');
      const input = document.getElementById('queryInput');
      const progress = document.getElementById('progress');
      const summaries = document.getElementById('summaries');
      const errorDiv = document.getElementById('error');
      form.onsubmit = function(e) {
        e.preventDefault();
        progress.innerHTML = '<div class="spinner-border text-primary" role="status"></div> <span>Processing...</span>';
        summaries.innerHTML = '';
        errorDiv.classList.add('d-none');
        const query = input.value;
        const evtSource = new EventSource(`/stream?query=${encodeURIComponent(query)}`);
        evtSource.onmessage = function(event) {
          const data = JSON.parse(event.data);
          if (data.type === 'progress') {
            progress.innerHTML = `<div class='spinner-border text-primary' role='status'></div> <span>${data.message}</span>`;
          } else if (data.type === 'summary') {
            progress.innerHTML = '';
            const card = document.createElement('div');
            card.className = 'card summary-card';
            card.innerHTML = `
              <div class="card-header">
                <a href="${data.url}" target="_blank">${data.title}</a>
                <button class="btn btn-outline-secondary btn-sm float-end" onclick="navigator.clipboard.writeText(\`${data.summary.replace(/`/g, '\`')}\`)">Copy</button>
              </div>
              <div class="card-body"><pre style="white-space: pre-wrap;">${data.summary}</pre></div>
            `;
            summaries.appendChild(card);
          } else if (data.type === 'error') {
            progress.innerHTML = '';
            errorDiv.textContent = data.message;
            errorDiv.classList.remove('d-none');
            evtSource.close();
          } else if (data.type === 'done') {
            progress.innerHTML = '';
            evtSource.close();
          }
        };
        evtSource.onerror = function() {
          progress.innerHTML = '';
          errorDiv.textContent = 'An error occurred while streaming results.';
          errorDiv.classList.remove('d-none');
          evtSource.close();
        };
      };
    </script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  </body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(TEMPLATE)

@app.route('/stream')
def stream():
    query = request.args.get('query', '')
    def event_stream():
        if not is_valid_query(query):
            yield f'data: {json.dumps({"type": "error", "message": "❌ This is not a valid query. Please enter a web search question."})}\n\n'
            return
        yield f'data: {json.dumps({"type": "progress", "message": "Checking for similar queries..."})}\n\n'
        embedding = get_embedding(query)
        similar = get_similar(query, embedding)
        if similar:
            q, summary, sim = similar
            yield f'data: {json.dumps({"type": "progress", "message": f"Found similar past query (similarity {sim:.2f}): {q}"})}\n\n'
            # Parse summary into cards
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
                    yield f'data: {json.dumps({"type": "summary", "title": title, "url": url, "summary": summ.strip()})}\n\n'
            yield f'data: {json.dumps({"type": "done"})}\n\n'
            return
        yield f'data: {json.dumps({"type": "progress", "message": "Searching the web..."})}\n\n'
        results = search_and_scrape(query)
        if not results:
            yield f'data: {json.dumps({"type": "error", "message": "❌ No web results found. Please try a different query."})}\n\n'
            return
        for idx, (url, title, text) in enumerate(results):
            yield f'data: {json.dumps({"type": "progress", "message": f"Summarizing result {idx+1} of {len(results)}..."})}\n\n'
            summ = summarize_texts([(url, title, text)])
            summary = summ.replace(f'- [{title}]({url})', '').strip()
            yield f'data: {json.dumps({"type": "summary", "title": title, "url": url, "summary": summary})}\n\n'
        # Save the full summary for future similarity
        full_summary = summarize_texts(results)
        save_result(query, embedding, full_summary)
        yield f'data: {json.dumps({"type": "done"})}\n\n'
    return Response(stream_with_context(event_stream()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=False, threaded=True) 