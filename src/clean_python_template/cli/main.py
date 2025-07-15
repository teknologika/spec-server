import typer

app = typer.Typer()


@app.command()
def hello():
    """A sample CLI command."""
    print("Hello World")
