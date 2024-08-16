from dataclasses import dataclass
import dataclasses
from typing import AsyncIterator, Any, Callable
from . import types
import json

from .transport import Transport

JSON_RPC_VERSION = "2.0"
PROTOCOL_VERSION = 1


@dataclass
class JsonRpcRequest:
    jsonrpc: str
    id: str
    method: str
    params: dict[str, Any] | None = None


@dataclass
class JsonRpcResponse:
    jsonrpc: str
    id: str | None = None
    result: Any | None = None
    error: dict[str, Any] | None = None


@dataclass
class JsonRpcNotification:
    jsonrpc: str
    method: str
    params: dict[str, Any] | None = None

class Encoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)

class Protocol:
    def __init__(self, transport: Transport):
        self.transport = transport

    async def send(
        self, message: JsonRpcRequest | JsonRpcResponse | JsonRpcNotification
    ) -> None:
        try:
            serialized = json.dumps(message.__dict__, cls=Encoder)
            await self.transport.write(serialized)
        except Exception as e:
            error_response = JsonRpcResponse(
                jsonrpc=JSON_RPC_VERSION,
                id=None,
                error={"code": -32603, "message": "Internal error", "data": str(e)}
            )
            await self.transport.write(json.dumps(error_response.__dict__), cls=Encoder)

    async def receive_frame(
        self,
    ) -> AsyncIterator[JsonRpcRequest | JsonRpcResponse | JsonRpcNotification]:
        while True:
            try:
                raw_message = await self.transport.read()
                parsed = json.loads(raw_message)

                if "method" in parsed:
                    if "id" in parsed:
                        yield JsonRpcRequest(**parsed)
                    else:
                        yield JsonRpcNotification(**parsed)
                elif "id" in parsed:
                    yield JsonRpcResponse(**parsed)
                else:
                    raise ValueError("Invalid JSON-RPC message")

            except json.JSONDecodeError:
                error_response = JsonRpcResponse(
                    jsonrpc=JSON_RPC_VERSION,
                    id=None,
                    error={"code": -32700, "message": "Parse error"}
                )
                await self.transport.write(json.dumps(error_response.__dict__), cls=Encoder)

            except Exception as e:
                error_response = JsonRpcResponse(
                    jsonrpc=JSON_RPC_VERSION,
                    id=None,
                    error={"code": -32603, "message": "Internal error", "data": str(e)}
                )
                await self.transport.write(json.dumps(error_response.__dict__), cls=Encoder)

    async def receive(self) -> Any:
        async for frame in self.receive_frame():
            if isinstance(frame, JsonRpcRequest):
                match frame.method:
                    case types.RequestType.Initialize.value:
                        return types.InitializeParams(**frame.params)
                    case types.RequestType.CallTool.value:
                        return types.CallToolParams(**frame.params)
                    case types.RequestType.ResourcesUnsubscribe.value:
                        return types.ResourcesUnsubscribeParams(**frame.params)
                    case types.RequestType.ResourcesSubscribe.value:
                        return types.ResourcesSubscribeParams(**frame.params)
                    case types.RequestType.ResourcesRead.value:
                        return types.ResourcesReadParams(**frame.params)
                    case types.RequestType.ResourcesList.value:
                        return None  # No params for ResourcesList
                    case types.RequestType.LoggingSetLevel.value:
                        return types.LoggingSetLevelParams(**frame.params)
                    case types.RequestType.PromptsGet.value:
                        return types.PromptsGetParams(**frame.params)
                    case types.RequestType.PromptsList.value:
                        return None  # No params for PromptsList
                    case _:
                        raise ValueError(f"Unknown method: {frame.method}")
            elif isinstance(frame, JsonRpcNotification):
                match frame.method:
                    case types.NotificationType.Initialized.value:
                        return None  # No params for Initialized notification
                    case types.NotificationType.Progress.value:
                        return types.ProgressParams(**frame.params)
                    case _:
                        raise ValueError(f"Unknown notification: {frame.method}")
            else:
                return frame  # Return JsonRpcResponse as-is

class ContextServer:
    def __init__(self, name: str):
        self.name = name
        self.prompts_list_handler = None
        self.prompt_get_handler = None

    def prompt_list(self):
        def decorator(func: Callable[[], list[types.PromptInfo]]):
            self.prompts_list_handler = func
            return func
        return decorator

    def prompt_get(self):
        def decorator(func: Callable[[str, dict[str, str] | None], str]):
            self.prompt_get_handler = func
            return func
        return decorator

    async def initialize(self, protocol: Protocol) -> None:
        # Wait for the initial Initialize request
        import importlib.metadata
        version = importlib.metadata.version("context-server")

        frame = await anext(protocol.receive_frame())
        if not isinstance(frame, JsonRpcRequest) or frame.method != types.RequestType.Initialize.value:
            raise ValueError("Expected Initialize request")

        params = types.InitializeParams(**frame.params)
        capabilities = types.ServerCapabilities(prompts={})
        server_info = types.EntityInfo(name=self.name, version=version)
        response = types.InitializeResponse(
            protocol_version=PROTOCOL_VERSION,
            capabilities=capabilities,
            server_info=server_info
        )
        await protocol.send(JsonRpcResponse(jsonrpc=JSON_RPC_VERSION, id=frame.id, result=response))

        # Wait for initialized notification
        frame = await anext(protocol.receive_frame())
        if not isinstance(frame, JsonRpcNotification) or frame.method != types.NotificationType.Initialized.value:
            raise ValueError("Expected Initialized notification")

        # Send initialized notification
        await protocol.send(JsonRpcNotification(jsonrpc=JSON_RPC_VERSION, method=types.NotificationType.Initialized.value))

    async def run(self, transport: Transport):
        protocol = Protocol(transport)
        await self.initialize(protocol)
        async for message in protocol.receive_frame():
            if isinstance(message, JsonRpcRequest):
                match message.method:
                    case types.RequestType.PromptsList.value:
                        if self.prompts_list_handler:
                            result = self.prompts_list_handler()
                            response = JsonRpcResponse(jsonrpc=JSON_RPC_VERSION, id=message.id, result=result)
                            await protocol.send(response)
                    case types.RequestType.PromptsGet.value:
                        if self.prompt_get_handler:
                            params = types.PromptsGetParams(**message.params)
                            result = self.prompt_get_handler(params.name, params.arguments)
                            response = JsonRpcResponse(jsonrpc=JSON_RPC_VERSION, id=message.id, result=result)
                            await protocol.send(response)
                    case types.RequestType.Initialize.value:
                        error_response = JsonRpcResponse(
                            jsonrpc=JSON_RPC_VERSION,
                            id=message.id,
                            error={"code": -32600, "message": "Invalid Request: Initialize not allowed"}
                        )
                        await protocol.send(error_response)
                    case _:
                        error_response = JsonRpcResponse(
                            jsonrpc=JSON_RPC_VERSION,
                            id=message.id,
                            error={"code": -32601, "message": "Method not found"}
                        )
                        await protocol.send(error_response)
            elif isinstance(message, JsonRpcNotification):
                if message.method == types.NotificationType.Initialized.value:
                    error_response = JsonRpcResponse(
                        jsonrpc=JSON_RPC_VERSION,
                        id=None,
                        error={"code": -32600, "message": "Invalid Request: Initialized notification not allowed"}
                    )
                    await protocol.send(error_response)
