from . import transport
import anyio

class FileAndStdioTransport(transport.Transport):
    def __init__(self, input_file: str):
        self.input_file = input_file
        self.input_stream = open(self.input_file, 'r')

    async def read(self) -> str:
        line = await anyio.to_thread.run_sync(self.input_stream.readline)
        if not line:
            return await anyio.to_thread.run_sync(input)
        return line.strip()

    async def write(self, message: str) -> None:
        print(message, flush=True)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await anyio.to_thread.run_sync(self.input_stream.close)
