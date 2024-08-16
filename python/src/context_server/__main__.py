from . import server, types, transport
from pathlib import Path
import click
import anyio

app = server.ContextServer(__name__)

@app.prompt_list()
def list() -> list[types.PromptInfo]:
    return []

@click.group()
def cli():
    pass

@cli.command()
def serve():
    anyio.run(app.run, transport.Stdio())

@cli.command()
@click.argument('file', type=click.Path(file_okay=True,dir_okay=False,exists=True, path_type=Path))
def debug_serve(file: Path):
    from . import debug
    async def run():
        async with debug.FileAndStdioTransport(file) as trans:
            await app.run(trans)
    anyio.run(run)

if __name__ == '__main__':
    cli()
