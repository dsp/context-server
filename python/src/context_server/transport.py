from abc import ABC, abstractmethod
import anyio


class Transport(ABC):
    @abstractmethod
    async def read(self) -> str:
        pass

    @abstractmethod
    async def write(self, message: str) -> None:
        pass


class Stdio(Transport):
    async def read(self) -> str:
        return await anyio.to_thread.run_sync(input)

    async def write(self, message: str) -> None:
        print(message, flush=True)
