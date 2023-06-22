#!/usr/bin/env python3

from pathlib import Path
from typing import Optional, List

import chromadb
import click
import requests
from click import Context
from langchain.document_loaders import UnstructuredPDFLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.vectorstores import Chroma
from pycomfort.files import traverse
from pynction import Try
from getpaper.download import try_download_async, download_papers


@click.group(invoke_without_command=False)
@click.pass_context
def app(ctx: Context):
    if ctx.invoked_subcommand is None:
        click.echo('Running the default command...')
    pass


@app.command("download_papers_async")
@click.argument('dois', nargs=-1)
@click.option('--threads', '-t', type=int, default=5, help='Number of threads (default: 5)')
def download_papers_async_command(dois: List[str], threads: int):
    """Downloads papers with the given DOIs to the specified destination."""
    if not dois:
        dois = ["10.3390/ijms22031073","wrong_doi", "10.1038/s41597-020-00710-z"]
    # Call the actual function with the provided arguments
    where = Path("./data/output/test/papers").absolute().resolve()
    results = download_papers(dois, where, threads)
    for k,v in results[0].items():
        print(f"successfully downloaded {k} in an async way to {v}")
    for w in results[1]:
        print(f"failed download for {w}")
    return results

def doi_download_parse(doi: str = "10.3390/ijms22031073", strategy: str = "auto"):
    print("example_download_and_parse_doi")
    from getpaper.download import try_download
    from getpaper.parse import parse_paper
    where = Path("./data/output/test/papers").absolute().resolve()
    try_download: Try[Path] = try_download(doi, where)
    return try_download.run(lambda p: parse_paper(p.absolute().resolve(), strategy=strategy), lambda f: "it crashed :((((((")

@app.command("doi_download_parse")
@click.option('--doi', type=click.STRING, default = "10.3390/ijms22031073", help="download doi")
@click.option("--strategy", type=click.Choice(["auto", "hi_res", "fast"]), default = "auto", help="strategy used to convert the page")
def doi_download_parse_command(doi: str = "10.3390/ijms22031073", strategy: str = "auto"):
   return doi_download_parse(doi, strategy)


@app.command("doi_download_parse_index")
@click.option('--doi', type=click.STRING, default = "10.3390/ijms22031073", help="download doi")
@click.option("--strategy", type=click.Choice(["auto", "hi_res", "fast"]), default = "auto", help="strategy used to convert the page")
def doi_download_parse_index(doi: str, strategy: str = "auto"):
    test_folder = Path("./data/output/test").absolute().resolve()
    download = doi_download_parse(doi, strategy)
    from getpaper.index import index_papers
    collection_name = "example"
    index = index_papers(test_folder / "papers", test_folder / "index", "example", 6000, "openai")
    print(f"Chroma index saved to {index}, now testing what it stored there")
    embeddings = OpenAIEmbeddings()
    example_db: Chroma = Chroma(collection_name=collection_name, persist_directory=str(index), embedding_function=embeddings)
    client: chromadb.Client = example_db._client
    example_collection = client.get_collection(collection_name, embeddings)
    print(f"printing part of the collection content of length {example_collection.count()}")
    top_5 = example_collection.get(limit=5, include=["embeddings", "metadatas", "documents"])
    print(f"TOP-5 IS {top_5}")



if __name__ == '__main__':
    app()