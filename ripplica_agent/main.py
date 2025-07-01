import click
from query_validator import is_valid_query
from embeddings import get_embedding
from storage import get_similar, save_result
from search_scraper import search_and_scrape
from summarizer import summarize_texts

@click.group()
def cli():
    """Web Query Agent: Search, summarize, and remember your queries!"""
    pass

@cli.command()
@click.argument('query')
@click.option('--debug', is_flag=True, help='Show debug output')
def ask(query, debug):
    """Ask a question to the web query agent."""
    click.secho(f"\n🕵️  Query: {query}", fg='cyan')
    if not is_valid_query(query):
        click.secho("❌ This is not a valid query. Please enter a web search question.", fg='red')
        return
    embedding = get_embedding(query)
    similar = get_similar(query, embedding)
    if similar:
        q, summary, sim = similar
        click.secho(f"\n🔎 Found a similar past query (similarity {sim:.2f}):", fg='yellow')
        click.secho(f"  {q}", fg='yellow')
        click.secho(f"\n📄 Summary:\n", fg='green')
        click.echo(summary)
        return
    click.secho("\n🌐 Searching the web...", fg='cyan')
    results = search_and_scrape(query, debug=debug)
    if not results:
        click.secho("❌ No web results found. Please try a different query.", fg='red')
        return
    if debug:
        click.secho(f"Scraped {len(results)} results:", fg='magenta')
        for url, text in results:
            click.secho(f"URL: {url} (text length: {len(text)})", fg='magenta')
    click.secho("\n📝 Summarizing results...", fg='cyan')
    summary = summarize_texts(results, debug=debug)
    if not summary.strip():
        click.secho("❌ Summary could not be generated. The web pages may have had little or no readable content.", fg='red')
    else:
        click.secho(f"\n📄 Summary:\n", fg='green')
        click.echo(summary)
    save_result(query, embedding, summary)

if __name__ == '__main__':
    cli() 