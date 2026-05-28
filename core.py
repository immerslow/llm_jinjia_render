import json
from collections.abc import Mapping
from urllib.parse import urlparse

import requests
from jinja2 import Environment, ChainableUndefined


# ============================================================
# Presets
# ============================================================
PRESETS = {
    "纯消息": json.dumps([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi! How can I help you?"},
        {"role": "user", "content": "What is the capital of France?"},
    ], indent=2, ensure_ascii=False),
    "消息 + 工具": json.dumps({
        "messages": [
            {"role": "system", "content": "You are a helpful assistant with access to tools."},
            {"role": "user", "content": "What's the weather like in Beijing?"},
            {"role": "assistant", "content": "", "tool_calls": [
                {"type": "function", "function": {"name": "get_weather", "arguments": '{"location": "Beijing"}'}}
            ]},
            {"role": "tool", "content": '{"temperature": 22, "condition": "sunny"}', "name": "get_weather"},
            {"role": "assistant", "content": "The weather in Beijing is currently 22°C and sunny."},
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "City name"},
                        },
                        "required": ["location"],
                    },
                },
            }
        ],
    }, indent=2, ensure_ascii=False),
    "多模态示例": json.dumps([
        {"role": "user", "content": [
            {"type": "image", "url": "https://example.com/image.jpg"},
            {"type": "text", "text": "Describe this image"},
        ]},
        {"role": "assistant", "content": "This is a beautiful landscape with mountains."},
    ], indent=2, ensure_ascii=False),
    "自定义": "",
}


# ============================================================
# URL helpers
# ============================================================
def parse_model_url(url: str):
    """Parse a HuggingFace or ModelScope model page URL.

    Returns (platform, owner, repo) or None.
    """
    url = url.strip().rstrip("/")
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if "huggingface.co" in host:
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) >= 2:
            return "huggingface", parts[0], parts[1]

    if "modelscope.cn" in host:
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) >= 3 and parts[0] == "models":
            return "modelscope", parts[1], parts[2]

    return None


def build_raw_url(platform: str, owner: str, repo: str, filename: str) -> str:
    """Build raw file download URL for a given platform."""
    if platform == "huggingface":
        return f"https://huggingface.co/{owner}/{repo}/raw/main/{filename}"
    if platform == "modelscope":
        return f"https://modelscope.cn/models/{owner}/{repo}/resolve/master/{filename}"
    raise ValueError(f"Unknown platform: {platform}")


def fetch_content(url: str, token: str | None = None) -> str:
    """Fetch text content from a URL with optional Bearer token."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text


def resolve_template(url: str, token: str | None = None) -> tuple[str, str]:
    """Fetch chat template from a URL.

    Strategy:
    1. If URL points directly to a .jinja / .json file, fetch it.
    2. Otherwise treat as model page: try chat_template.jinja first,
       then fall back to tokenizer_config.json.

    Returns (template_content, source_description).
    """
    url = url.strip().rstrip("/")

    if url.endswith((".jinja", ".json")):
        content = fetch_content(url, token)
        name = url.rsplit("/", 1)[-1]
        if name == "tokenizer_config.json":
            data = json.loads(content)
            if "chat_template" not in data:
                raise ValueError("tokenizer_config.json 中未找到 chat_template 字段")
            return data["chat_template"], "tokenizer_config.json"
        return content, name

    parsed = parse_model_url(url)
    if not parsed:
        raise ValueError("无法解析 URL，请检查格式")

    platform, owner, repo = parsed

    jinja_url = build_raw_url(platform, owner, repo, "chat_template.jinja")
    try:
        content = fetch_content(jinja_url, token)
        return content, "chat_template.jinja"
    except requests.HTTPError:
        config_url = build_raw_url(platform, owner, repo, "tokenizer_config.json")
        config_text = fetch_content(config_url, token)
        data = json.loads(config_text)
        if "chat_template" not in data:
            raise ValueError("tokenizer_config.json 中未找到 chat_template 字段")
        return data["chat_template"], "tokenizer_config.json"


# ============================================================
# Jinja rendering
# ============================================================
def _safe_items(value):
    """Custom ``items`` filter that tolerates JSON strings and non-mappings.

    The default Jinja2 ``|items`` filter raises RuntimeError when the
    input is not a Mapping.  Many HuggingFace chat templates apply
    ``|items`` to ``tool_call.arguments``, which may be a JSON-encoded
    string rather than a dict.  This filter transparently handles that.
    """
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    if isinstance(value, Mapping):
        return value.items()
    return []


def render_template(
    template_str: str,
    messages: list,
    add_generation_prompt: bool = False,
    tools: list | None = None,
    cleanup_whitespace: bool = True,
) -> str:
    """Render a Jinja2 chat template with the given messages and tools."""
    if cleanup_whitespace:
        lines = template_str.split("\n")
        cleaned = []
        prev_empty = False
        for line in lines:
            s = line.strip()
            if not s:
                if not prev_empty:
                    cleaned.append("")
                prev_empty = True
            else:
                cleaned.append(s)
                prev_empty = False
        template_str = "\n".join(cleaned)

    env = Environment(undefined=ChainableUndefined, autoescape=False)
    env.filters["items"] = _safe_items
    template = env.from_string(template_str)

    context = {
        "messages": messages,
        "add_generation_prompt": add_generation_prompt,
        "bos_token": "",
        "eos_token": "",
    }
    if tools:
        context["tools"] = tools

    return template.render(**context)
