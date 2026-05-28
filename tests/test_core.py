"""Tests for core.py — URL helpers, template resolution, Jinja rendering."""

import json
from unittest.mock import MagicMock, patch

import pytest
from jinja2 import ChainableUndefined

from core import (
    PRESETS,
    _safe_items,
    build_raw_url,
    fetch_content,
    parse_model_url,
    render_template,
    resolve_template,
)


# ============================================================
# parse_model_url
# ============================================================
class TestParseModelURL:
    def test_huggingface_standard(self):
        result = parse_model_url("https://huggingface.co/openbmb/MiniCPM5-1B/")
        assert result == ("huggingface", "openbmb", "MiniCPM5-1B")

    def test_huggingface_no_trailing_slash(self):
        result = parse_model_url("https://huggingface.co/Qwen/Qwen2.5-7B-Instruct")
        assert result == ("huggingface", "Qwen", "Qwen2.5-7B-Instruct")

    def test_huggingface_with_raw_path(self):
        result = parse_model_url("https://huggingface.co/Qwen/Qwen3.5-9B/raw/main/chat_template.jinja")
        assert result == ("huggingface", "Qwen", "Qwen3.5-9B")

    def test_huggingface_with_blob_path(self):
        result = parse_model_url("https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/main/tokenizer_config.json")
        assert result == ("huggingface", "Qwen", "Qwen2.5-7B-Instruct")

    def test_modelscope_standard(self):
        result = parse_model_url("https://modelscope.cn/models/NemoStation/Marlin-2B")
        assert result == ("modelscope", "NemoStation", "Marlin-2B")

    def test_modelscope_with_resolve_path(self):
        result = parse_model_url("https://modelscope.cn/models/NemoStation/Marlin-2B/resolve/master/chat_template.jinja")
        assert result == ("modelscope", "NemoStation", "Marlin-2B")

    def test_modelscope_with_trailing_slash(self):
        result = parse_model_url("https://modelscope.cn/models/NemoStation/Marlin-2B/")
        assert result == ("modelscope", "NemoStation", "Marlin-2B")

    def test_unknown_host_returns_none(self):
        result = parse_model_url("https://example.com/models/foo/bar")
        assert result is None

    def test_unknown_huggingface_short_path(self):
        result = parse_model_url("https://huggingface.co/single-name")
        assert result is None

    def test_modelscope_wrong_prefix(self):
        result = parse_model_url("https://modelscope.cn/repo/NemoStation/Marlin-2B")
        assert result is None

    def test_empty_string(self):
        result = parse_model_url("")
        assert result is None

    def test_whitespace_stripped(self):
        result = parse_model_url("  https://huggingface.co/Qwen/Qwen3-8B/  ")
        assert result == ("huggingface", "Qwen", "Qwen3-8B")


# ============================================================
# build_raw_url
# ============================================================
class TestBuildRawURL:
    def test_huggingface_jinja(self):
        url = build_raw_url("huggingface", "Qwen", "Qwen3-8B", "chat_template.jinja")
        assert url == "https://huggingface.co/Qwen/Qwen3-8B/raw/main/chat_template.jinja"

    def test_huggingface_json(self):
        url = build_raw_url("huggingface", "Qwen", "Qwen3-8B", "tokenizer_config.json")
        assert url == "https://huggingface.co/Qwen/Qwen3-8B/raw/main/tokenizer_config.json"

    def test_modelscope_jinja(self):
        url = build_raw_url("modelscope", "NemoStation", "Marlin-2B", "chat_template.jinja")
        assert url == "https://modelscope.cn/models/NemoStation/Marlin-2B/resolve/master/chat_template.jinja"

    def test_unknown_platform_raises(self):
        with pytest.raises(ValueError, match="Unknown platform"):
            build_raw_url("unknown", "owner", "repo", "file.txt")


# ============================================================
# fetch_content (mocked)
# ============================================================
class TestFetchContent:
    @patch("core.requests.get")
    def test_basic_fetch(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = "hello"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = fetch_content("https://example.com/file.txt")
        assert result == "hello"
        mock_get.assert_called_once_with("https://example.com/file.txt", headers={}, timeout=15)

    @patch("core.requests.get")
    def test_fetch_with_token(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = "secret"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = fetch_content("https://example.com/file.txt", token="abc123")
        assert result == "secret"
        mock_get.assert_called_once_with(
            "https://example.com/file.txt",
            headers={"Authorization": "Bearer abc123"},
            timeout=15,
        )

    @patch("core.requests.get")
    def test_fetch_http_error(self, mock_get):
        import requests as _requests
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = _requests.HTTPError("404")
        mock_get.return_value = mock_resp

        with pytest.raises(_requests.HTTPError):
            fetch_content("https://example.com/not-found.txt")


# ============================================================
# resolve_template (mocked)
# ============================================================
class TestResolveTemplate:
    @patch("core.fetch_content")
    def test_direct_jinja_url(self, mock_fetch):
        mock_fetch.return_value = "{% for m in messages %}{{ m }}{% endfor %}"
        content, source = resolve_template(
            "https://huggingface.co/Qwen/Qwen3/raw/main/chat_template.jinja"
        )
        assert content == mock_fetch.return_value
        assert source == "chat_template.jinja"

    @patch("core.fetch_content")
    def test_direct_tokenizer_config_json(self, mock_fetch):
        config = {"chat_template": "{% for m in messages %}{{ m }}{% endfor %}"}
        mock_fetch.return_value = json.dumps(config)
        content, source = resolve_template(
            "https://huggingface.co/Qwen/Qwen3/raw/main/tokenizer_config.json"
        )
        assert content == config["chat_template"]
        assert source == "tokenizer_config.json"

    @patch("core.fetch_content")
    def test_direct_tokenizer_config_no_chat_template(self, mock_fetch):
        mock_fetch.return_value = json.dumps({"model_type": "qwen"})
        with pytest.raises(ValueError, match="未找到 chat_template 字段"):
            resolve_template(
                "https://huggingface.co/Qwen/Qwen3/raw/main/tokenizer_config.json"
            )

    @patch("core.fetch_content")
    def test_model_page_jinja_found(self, mock_fetch):
        mock_fetch.return_value = "jinja content"
        content, source = resolve_template("https://huggingface.co/Qwen/Qwen3/")
        assert content == "jinja content"
        assert source == "chat_template.jinja"
        # First call should be for chat_template.jinja
        call_url = mock_fetch.call_args_list[0][0][0]
        assert "chat_template.jinja" in call_url

    @patch("core.fetch_content")
    def test_model_page_jinja_fallback_to_config(self, mock_fetch):
        import requests as _requests

        # First call (chat_template.jinja) fails, second (tokenizer_config.json) succeeds
        config = {"chat_template": "fallback content"}
        call_count = 0

        def side_effect(url, token=None):
            nonlocal call_count
            call_count += 1
            if "chat_template.jinja" in url:
                raise _requests.HTTPError("404")
            return json.dumps(config)

        mock_fetch.side_effect = side_effect
        content, source = resolve_template("https://modelscope.cn/models/NemoStation/Marlin-2B")
        assert content == "fallback content"
        assert source == "tokenizer_config.json"

    @patch("core.fetch_content")
    def test_model_page_no_template_found(self, mock_fetch):
        import requests as _requests

        def side_effect(url, token=None):
            if "chat_template.jinja" in url:
                raise _requests.HTTPError("404")
            return json.dumps({"model_type": "llama"})

        mock_fetch.side_effect = side_effect
        with pytest.raises(ValueError, match="未找到 chat_template 字段"):
            resolve_template("https://huggingface.co/some/model/")

    def test_invalid_url(self):
        with pytest.raises(ValueError, match="无法解析 URL"):
            resolve_template("not-a-url")


# ============================================================
# render_template
# ============================================================
class TestRenderTemplate:
    def test_simple_loop(self):
        tpl = "{% for m in messages %}{{ m['role'] }}: {{ m['content'] }}\n{% endfor %}"
        msgs = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]
        result = render_template(tpl, msgs)
        assert "user: hi" in result
        assert "assistant: hello" in result

    def test_add_generation_prompt(self):
        tpl = "{% for m in messages %}{{ m['role'] }}\n{% endfor %}{% if add_generation_prompt %}assistant\n{% endif %}"
        msgs = [{"role": "user", "content": "hi"}]
        result_off = render_template(tpl, msgs, add_generation_prompt=False)
        result_on = render_template(tpl, msgs, add_generation_prompt=True)
        assert "assistant\n" not in result_off
        assert "assistant\n" in result_on

    def test_tools_in_context(self):
        tpl = "{% if tools %}has tools: {{ tools | length }}{% endif %}"
        msgs = [{"role": "user", "content": "hi"}]
        tools = [{"type": "function", "function": {"name": "test"}}]
        result = render_template(tpl, msgs, tools=tools)
        assert "has tools: 1" in result

    def test_no_tools_not_in_context(self):
        tpl = "{% if tools %}HAS_TOOLS{% else %}NO_TOOLS{% endif %}"
        msgs = [{"role": "user", "content": "hi"}]
        result = render_template(tpl, msgs)
        assert "NO_TOOLS" in result

    def test_cleanup_whitespace(self):
        # Template has line-level leading/trailing spaces and blank lines.
        # cleanup_whitespace strips each line and collapses consecutive blanks.
        tpl = "  {% for m in messages %}  \n  {{ m['content'] }}  \n\n\n  {% endfor %}  "
        msgs = [{"role": "user", "content": "hi"}]
        result = render_template(tpl, msgs, cleanup_whitespace=True)
        assert "hi" in result

    def test_cleanup_collapses_blank_lines(self):
        # Multiple blank lines collapse to at most one
        tpl = "A\n\n\n\nB"
        msgs = []
        result = render_template(tpl, msgs, cleanup_whitespace=True)
        # 3 consecutive blank lines → 1 blank line → output has at most one \n\n
        assert result.count("\n\n") == 1
        assert "A" in result and "B" in result

    def test_no_cleanup_whitespace(self):
        tpl = "  hello  \n  world  "
        msgs = []
        result = render_template(tpl, msgs, cleanup_whitespace=False)
        assert "  hello  " in result

    def test_empty_messages(self):
        tpl = "{% for m in messages %}{{ m }}{% endfor %}"
        result = render_template(tpl, [])
        assert result.strip() == ""

    def test_unknown_variable_undefined(self):
        tpl = "{{ undefined_var }}"
        result = render_template(tpl, [])
        # ChainableUndefined renders as empty string
        assert result.strip() == ""

    def test_bos_eos_tokens(self):
        tpl = "{% if bos_token %}[BOS]{% endif %}{% for m in messages %}{{ m['content'] }}{% endfor %}{% if eos_token %}[EOS]{% endif %}"
        msgs = [{"role": "user", "content": "hi"}]
        result = render_template(tpl, msgs)
        # bos_token and eos_token are empty strings, so the if-blocks are skipped
        assert "[BOS]" not in result
        assert "[EOS]" not in result

    def test_multimodal_content(self):
        tpl = "{% for m in messages %}{% if m['content'] is string %}{{ m['content'] }}{% else %}MULTIMODAL{% endif %}{% endfor %}"
        msgs = [
            {"role": "user", "content": [
                {"type": "image", "url": "https://example.com/img.jpg"},
                {"type": "text", "text": "describe"},
            ]},
        ]
        result = render_template(tpl, msgs)
        assert "MULTIMODAL" in result


# ============================================================
# _safe_items filter
# ============================================================
class TestSafeItems:
    def test_dict_input(self):
        result = list(_safe_items({"a": 1, "b": 2}))
        assert result == [("a", 1), ("b", 2)]

    def test_json_string_input(self):
        result = list(_safe_items('{"x": 10, "y": 20}'))
        assert result == [("x", 10), ("y", 20)]

    def test_invalid_json_string_returns_empty(self):
        result = list(_safe_items("not json"))
        assert result == []

    def test_empty_string_returns_empty(self):
        result = list(_safe_items(""))
        assert result == []

    def test_list_input_returns_empty(self):
        result = list(_safe_items([1, 2, 3]))
        assert result == []

    def test_none_input_returns_empty(self):
        result = list(_safe_items(None))
        assert result == []

    def test_integer_input_returns_empty(self):
        result = list(_safe_items(42))
        assert result == []


# ============================================================
# Integration: render with tools + items filter
# ============================================================
class TestRenderWithTools:
    """Verify that the |items filter works correctly in realistic templates."""

    def test_qwen_style_items_on_arguments(self):
        """Simulates the Qwen template pattern:
        {% for args_name, args_value in tool_call.arguments|items %}
        """
        tpl = (
            "{% for m in messages %}"
            "{% if m.get('tool_calls') %}"
            "{% for tc in m['tool_calls'] %}"
            "{% for k, v in tc['function']['arguments']|items %}"
            "{{ k }}={{ v }} "
            "{% endfor %}"
            "{% endfor %}"
            "{% endif %}"
            "{% endfor %}"
        )
        msgs = [
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "Beijing"}',
                        },
                    }
                ],
            }
        ]
        result = render_template(tpl, msgs)
        assert "location=Beijing" in result

    def test_items_on_dict(self):
        tpl = "{% for k, v in data|items %}{{ k }}{% endfor %}"
        result = render_template(tpl, [], tools=None)
        # tools is None, but we pass 'data' via context — need different approach
        # Actually, let's use a different variable
        tpl2 = "{% set d = {'a': 1} %}{% for k, v in d|items %}{{ k }}{% endfor %}"
        result2 = render_template(tpl2, [])
        assert "a" in result2

    def test_items_on_non_dict_returns_empty(self):
        tpl = "{% for k, v in 123|items %}{{ k }}{% endfor %}"
        result = render_template(tpl, [])
        assert result.strip() == ""

    def test_full_preset_with_tools_renders(self):
        """The full '消息+工具' preset should render without error."""
        preset_data = json.loads(PRESETS["消息 + 工具"])
        messages = preset_data["messages"]
        tools = preset_data["tools"]

        # Use a simple template that doesn't use |items
        tpl = "{% for m in messages %}{{ m['role'] }}: {{ m['content'] }}\n{% endfor %}"
        result = render_template(tpl, messages, tools=tools)
        assert "system:" in result
        assert "user:" in result
        assert "assistant:" in result

    def test_full_preset_with_items_template(self):
        """Template using |items on tool_call.arguments (Qwen pattern)."""
        tpl = (
            "{% for m in messages %}"
            "{% if m.get('tool_calls') %}"
            "{% for tc in m['tool_calls'] %}"
            "CALL:{{ tc['function']['name'] }} "
            "{% for k, v in tc['function']['arguments']|items %}"
            "{{ k }}={{ v }}"
            "{% endfor %}"
            "\n"
            "{% endfor %}"
            "{% endif %}"
            "{% endfor %}"
        )
        preset_data = json.loads(PRESETS["消息 + 工具"])
        messages = preset_data["messages"]
        tools = preset_data["tools"]

        result = render_template(tpl, messages, tools=tools)
        assert "CALL:get_weather" in result
        assert "location=Beijing" in result


# ============================================================
# PRESETS
# ============================================================
class TestPresets:
    def test_all_presets_are_valid_json_or_empty(self):
        for name, value in PRESETS.items():
            if name == "自定义":
                assert value == ""
            else:
                parsed = json.loads(value)
                assert isinstance(parsed, (list, dict))

    def test_pure_messages_is_list(self):
        data = json.loads(PRESETS["纯消息"])
        assert isinstance(data, list)
        assert all(isinstance(m, dict) for m in data)
        assert all("role" in m for m in data)

    def test_messages_with_tools_is_dict(self):
        data = json.loads(PRESETS["消息 + 工具"])
        assert isinstance(data, dict)
        assert "messages" in data
        assert "tools" in data
        assert isinstance(data["messages"], list)
        assert isinstance(data["tools"], list)

    def test_multimodal_is_list(self):
        data = json.loads(PRESETS["多模态示例"])
        assert isinstance(data, list)
        # First message has a list content (multimodal)
        assert isinstance(data[0]["content"], list)
