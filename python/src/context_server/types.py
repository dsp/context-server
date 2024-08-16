from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class RequestType(StrEnum):
    Initialize = "initialize"
    CallTool = "tools/call"
    ResourcesUnsubscribe = "resources/unsubscribe"
    ResourcesSubscribe = "resources/subscribe"
    ResourcesRead = "resources/read"
    ResourcesList = "resources/list"
    LoggingSetLevel = "logging/setLevel"
    PromptsGet = "prompts/get"
    PromptsList = "prompts/list"


@dataclass
class ClientCapabilities:
    experimental: dict[str, Any] | None = None
    sampling: dict[str, Any] | None = None


@dataclass
class EntityInfo:
    name: str
    version: str


@dataclass
class InitializeParams:
    protocol_version: int
    capabilities: ClientCapabilities
    client_info: EntityInfo


@dataclass
class ResourcesCapabilities:
    subscribe: bool | None = None


@dataclass
class ServerCapabilities:
    experimental: dict[str, Any] | None = None
    logging: dict[str, Any] | None = None
    prompts: dict[str, Any] | None = None
    resources: ResourcesCapabilities | None = None
    tools: dict[str, Any] | None = None


@dataclass
class InitializeResponse:
    protocol_version: int
    capabilities: ServerCapabilities
    server_info: EntityInfo


@dataclass
class CallToolParams:
    name: str
    arguments: Any | None = None


@dataclass
class ResourcesUnsubscribeParams:
    uri: str


@dataclass
class ResourcesSubscribeParams:
    uri: str


@dataclass
class ResourcesReadParams:
    uri: str


class LoggingLevel(StrEnum):
    Debug = "debug"
    Info = "info"
    Warning = "warning"
    Error = "error"


@dataclass
class LoggingSetLevelParams:
    level: LoggingLevel


@dataclass
class PromptsGetParams:
    name: str
    arguments: dict[str, str] | None = None


@dataclass
class ResourceContent:
    uri: str
    content_type: str
    mime_type: str | None = None
    text: str | None = None
    data: str | None = None


@dataclass
class ResourcesReadResponse:
    contents: list[ResourceContent]


@dataclass
class ResourceTemplate:
    uri_template: str
    name: str | None = None
    description: str | None = None


@dataclass
class Resource:
    uri: str
    mime_type: str | None = None


@dataclass
class ResourcesListResponse:
    resources: list[Resource]
    resource_templates: list[ResourceTemplate]


@dataclass
class PromptsGetResponse:
    prompt: str


@dataclass
class PromptArgument:
    name: str
    description: str | None = None
    required: bool | None = None


@dataclass
class PromptInfo:
    name: str
    arguments: list[PromptArgument] | None = None


@dataclass
class PromptsListResponse:
    prompts: list[PromptInfo]


@dataclass
class Tool:
    name: str
    input_schema: Any
    description: str | None = None


class NotificationType(StrEnum):
    Initialized = "notifications/initialized"
    Progress = "notifications/progress"


@dataclass
class ProgressParams:
    progress_token: str
    progress: float
    total: float | None = None


@dataclass
class ClientNotification:
    type: NotificationType
    params: ProgressParams | None = None
