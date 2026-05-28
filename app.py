import streamlit as st
import requests
import json
import base64
from string import Template

from streamlit_ace import st_ace
from streamlit_js_eval import streamlit_js_eval

from core import (
    PRESETS,
    build_raw_url,
    fetch_content,
    parse_model_url,
    render_template,
)

st.set_page_config(layout="wide", page_title="Jinja Render")

STYLE = {
    "bg": "#f7f7f4",
    "paper": "rgba(255, 255, 252, 0.96)",
    "paper_muted": "#f0f0ea",
    "ink": "#202326",
    "muted": "#666d73",
    "line": "#d8d8d2",
    "line_strong": "#b9b9b1",
    "accent": "#2f4f63",
    "accent_hover": "#243f50",
    "code_bg": "#f8f8f4",
    "button_height": "40px",
    "button_font_size": "14px",
    "button_font_weight": "500",
    "radius": "8px",
    "radius_lg": "12px",
    "shadow": "0 10px 28px rgba(31, 35, 39, 0.07)",
    "font_body": "'Noto Sans SC', 'LXGW WenKai GB Screen', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    "font_heading": "Lora, 'Noto Sans SC', 'LXGW WenKai GB Screen', Georgia, serif",
    "font_mono": "'LXGW WenKai GB Screen', 'Noto Sans Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
}

COPY_BUTTON_CSS = f"""
html, body {{
    margin: 0;
    padding: 0;
    overflow: hidden;
}}
.copy-button {{
    width: 100%;
    height: {STYLE['button_height']};
    border: 1px solid {STYLE['line_strong']};
    border-radius: {STYLE['radius']};
    color: {STYLE['ink']};
    background: {STYLE['paper']};
    box-shadow: none;
    font-family: {STYLE['font_body']};
    font-size: {STYLE['button_font_size']};
    font-weight: {STYLE['button_font_weight']};
    line-height: 1.2;
    cursor: pointer;
    transition: border-color 0.12s ease, background 0.12s ease, color 0.12s ease;
}}
.copy-button:hover {{
    color: {STYLE['accent']};
    border-color: {STYLE['accent']};
    background: #fbfbf8;
}}
"""

st.markdown(
    Template("""
    <style>
    @import url("https://cdn.jsdelivr.net/npm/lxgw-wenkai-screen-web/lxgwwenkaigbscreen/result.css");
    @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&family=Noto+Sans+SC:wght@100..900&display=swap');

    :root {
        --app-bg: $bg;
        --paper: $paper;
        --paper-muted: $paper_muted;
        --ink: $ink;
        --muted: $muted;
        --line: $line;
        --line-strong: $line_strong;
        --accent: $accent;
        --accent-hover: $accent_hover;
        --code-bg: $code_bg;
        --button-height: $button_height;
        --button-font-size: $button_font_size;
        --button-font-weight: $button_font_weight;
        --radius: $radius;
        --radius-lg: $radius_lg;
        --shadow: $shadow;
        --font-body: $font_body;
        --font-heading: $font_heading;
        --font-mono: $font_mono;
    }

    html, body, [class*="css"], .stApp {
        font-family: var(--font-body) !important;
    }

    .stApp {
        color: var(--ink);
        background: var(--app-bg);
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.4rem;
        padding-bottom: 2.5rem;
    }

    .app-hero {
        padding: 1.2rem 1.35rem;
        margin-bottom: 1.05rem;
        border: 1px solid var(--line);
        border-radius: var(--radius-lg);
        background: var(--paper);
        box-shadow: var(--shadow);
    }

    .app-kicker {
        color: var(--accent);
        font-family: var(--font-body);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }

    .app-title {
        color: var(--ink);
        font-family: var(--font-heading);
        font-size: clamp(1.8rem, 3.2vw, 2.8rem);
        line-height: 1.05;
        font-weight: 700;
        margin: 0;
    }

    .app-subtitle {
        max-width: 860px;
        color: var(--muted);
        font-family: var(--font-body);
        font-size: 1.02rem;
        line-height: 1.75;
        margin-top: 0.65rem;
        margin-bottom: 0;
    }

    div[data-testid="stHorizontalBlock"] {
        gap: 1rem;
    }

    div[data-testid="stHorizontalBlock"] > div {
        min-height: 0;
    }

    .section-card {
        padding: 1rem 1.05rem 1.1rem;
        margin-bottom: 1rem;
        border: 1px solid var(--line);
        border-radius: var(--radius-lg);
        background: var(--paper);
        box-shadow: var(--shadow);
    }

    .panel-title {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 0.75rem;
        min-height: 2.2rem;
        margin-bottom: 0.45rem;
    }

    .panel-title h3 {
        margin: 0;
        color: var(--ink);
        font-family: var(--font-heading);
        font-size: 1.1rem;
        line-height: 1.35;
    }

    .panel-title span {
        color: var(--muted);
        font-family: var(--font-body);
        font-size: 0.82rem;
        white-space: nowrap;
    }

    label, .stCheckbox label, .stSelectbox label, .stTextInput label {
        color: var(--muted) !important;
        font-family: var(--font-body) !important;
        font-size: 0.9rem !important;
    }

    .stTextInput input,
    .stSelectbox div[data-baseweb="select"] > div,
    .stTextArea textarea {
        font-family: var(--font-body) !important;
        border: 1px solid var(--line) !important;
        border-radius: var(--radius) !important;
        background: var(--paper) !important;
        box-shadow: none !important;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px rgba(47, 79, 99, 0.12) !important;
    }

    .stTextArea textarea {
        min-height: 460px !important;
        padding: 1rem !important;
        color: var(--ink) !important;
        background: var(--code-bg) !important;
        border-color: var(--line) !important;
        font-family: var(--font-mono) !important;
        font-size: 14px !important;
        line-height: 1.72 !important;
        caret-color: var(--accent) !important;
    }

    .stTextArea textarea:disabled {
        -webkit-text-fill-color: var(--ink) !important;
        opacity: 1 !important;
    }

    .stButton > button {
        height: var(--button-height);
        border: 1px solid var(--line-strong);
        border-radius: var(--radius);
        color: var(--ink);
        background: var(--paper);
        box-shadow: none;
        font-family: var(--font-body) !important;
        font-size: var(--button-font-size);
        font-weight: var(--button-font-weight);
        line-height: 1.2;
        transition: border-color 0.12s ease, background 0.12s ease, color 0.12s ease;
    }

    .stButton > button:hover {
        color: var(--accent);
        border-color: var(--accent);
        background: #fbfbf8;
    }

    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {
        color: #ffffff;
        border-color: var(--accent);
        background: var(--accent);
    }

    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {
        color: #ffffff;
        border-color: var(--accent-hover);
        background: var(--accent-hover);
    }

    .stCheckbox [data-testid="stMarkdownContainer"] p {
        color: var(--ink);
        font-family: var(--font-body);
        font-size: 0.94rem;
    }

    div[data-testid="stAlert"] {
        border-radius: var(--radius);
        border: 1px solid var(--line);
        background: var(--paper);
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--line) !important;
        border-radius: var(--radius-lg) !important;
        background: var(--paper) !important;
        box-shadow: var(--shadow) !important;
    }

    iframe[title="streamlit_ace.st_ace"] {
        border-radius: var(--radius);
        border: 1px solid var(--line);
        overflow: hidden;
    }

    .stMarkdown .caption {
        color: var(--muted);
        font-family: var(--font-body);
        font-size: 0.88rem;
        line-height: 1.65;
        margin-top: -0.35rem;
    }

    @media (max-width: 900px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; }
        .app-hero { padding: 1.1rem; }
        .stTextArea textarea { min-height: 340px !important; }
    }
    </style>
    """).substitute(STYLE),
    unsafe_allow_html=True,
)

# ============================================================
# Session state defaults
# ============================================================
if "jinja_content" not in st.session_state:
    st.session_state.jinja_content = ""
if "msg_content" not in st.session_state:
    st.session_state.msg_content = PRESETS["纯消息"]
if "prev_preset" not in st.session_state:
    st.session_state.prev_preset = "纯消息"
if "expanded_panel" not in st.session_state:
    st.session_state.expanded_panel = None
if "template_source_url" not in st.session_state:
    st.session_state.template_source_url = ""
if "rendered_result" not in st.session_state:
    st.session_state.rendered_result = ""
if "render_error" not in st.session_state:
    st.session_state.render_error = ""
if "frontend_fetch_key" not in st.session_state:
    st.session_state.frontend_fetch_key = 0
if "frontend_fetch_pending" not in st.session_state:
    st.session_state.frontend_fetch_pending = False
if "frontend_fetch_url" not in st.session_state:
    st.session_state.frontend_fetch_url = ""
if "frontend_fetch_token" not in st.session_state:
    st.session_state.frontend_fetch_token = ""
if "messages_editor_version" not in st.session_state:
    st.session_state.messages_editor_version = 0
if "jinja_editor_version" not in st.session_state:
    st.session_state.jinja_editor_version = 0
if "result_editor_version" not in st.session_state:
    st.session_state.result_editor_version = 0


def copy_button(label: str, text: str, key: str) -> None:
    payload = json.dumps(text or "")
    html = f"""
        <!doctype html>
        <meta charset="utf-8">
        <style>{COPY_BUTTON_CSS}</style>
        <button id="copy-{key}" class="copy-button">{label}</button>
        <script>
        const button = document.getElementById("copy-{key}");
        const text = {payload};
        button.onclick = async () => {{
            await navigator.clipboard.writeText(text);
            button.innerText = "已复制";
            setTimeout(() => button.innerText = {json.dumps(label)}, 1200);
        }};
        </script>
    """
    src = "data:text/html;charset=utf-8;base64," + base64.b64encode(html.encode("utf-8")).decode("ascii")
    st.iframe(src, height=44)


def expand_button(panel_key: str) -> None:
    current = st.session_state.get("expanded_panel")
    if current == panel_key:
        if st.button("收起", key=f"collapse_{panel_key}", use_container_width=True):
            st.session_state.expanded_panel = None
            st.rerun()
    elif st.button("放大", key=f"expand_{panel_key}", use_container_width=True):
        st.session_state.expanded_panel = panel_key
        st.rerun()


def code_editor(
    *,
    value: str,
    key: str,
    language: str,
    height: int,
    readonly: bool = False,
    auto_update: bool = True,
) -> str:
    edited = st_ace(
        value=value,
        language=language,
        theme="chrome",
        keybinding="vscode",
        height=height,
        font_size=14,
        tab_size=2,
        wrap=True,
        show_gutter=True,
        show_print_margin=False,
        readonly=readonly,
        auto_update=auto_update,
        key=key,
    )
    return value if edited is None else edited


def text_value(value: object) -> str:
    return value if isinstance(value, str) else ""


def reset_template_state() -> None:
    st.session_state.jinja_content = ""
    st.session_state.template_source_url = ""
    st.session_state.rendered_result = ""
    st.session_state.render_error = ""
    st.session_state.jinja_editor_version += 1
    st.session_state.result_editor_version += 1


def format_escaped_template(template: str) -> str:
    original = text_value(template)
    text = original.strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and isinstance(parsed.get("chat_template"), str):
            text = parsed["chat_template"]
        elif isinstance(parsed, str):
            text = parsed
        else:
            return original
    except json.JSONDecodeError:
        if text.count("\n") >= 3 or "\\n" not in text:
            return original

    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        try:
            decoded = json.loads(text)
            if isinstance(decoded, str):
                text = decoded
        except json.JSONDecodeError:
            text = text[1:-1]

    protected = {
        "\0ESCAPED_CRLF\0": "\\r\\n",
        "\0ESCAPED_LF\0": "\\n",
        "\0ESCAPED_TAB\0": "\\t",
    }

    # Preserve escapes that belong inside Jinja string literals, such as
    # {{ "...\\n" }}, while turning outer JSON-style line separators into
    # real newlines.
    text = (
        text.replace("\\\\r\\\\n", "\0ESCAPED_CRLF\0")
        .replace("\\\\n", "\0ESCAPED_LF\0")
        .replace("\\\\t", "\0ESCAPED_TAB\0")
    )

    text = (
        text.replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace('\\"', '"')
        .replace("\\'", "'")
    )

    for placeholder, escaped in protected.items():
        text = text.replace(placeholder, escaped)

    return text


def maybe_format_escaped_template(template: str) -> str:
    template = text_value(template)
    if "\\n" not in template:
        return template
    if template.count("\n") >= 3:
        return template
    return (
        format_escaped_template(template)
    )


def format_json_text(text: str) -> str:
    data = json.loads(text_value(text))
    return json.dumps(data, indent=2, ensure_ascii=False)


def enable_add_generation_prompt(text: str) -> str:
    data = json.loads(text_value(text)) if text_value(text).strip() else []
    if isinstance(data, list):
        data = {"messages": data, "add_generation_prompt": True}
    elif isinstance(data, dict):
        data["add_generation_prompt"] = True
    else:
        raise ValueError("消息 JSON 必须是数组或对象")
    return json.dumps(data, indent=2, ensure_ascii=False)


def apply_add_generation_prompt() -> tuple[bool, str | None]:
    try:
        st.session_state.msg_content = enable_add_generation_prompt(st.session_state.msg_content)
        st.session_state.rendered_result = ""
        st.session_state.render_error = ""
        st.session_state.messages_editor_version += 1
        st.session_state.result_editor_version += 1
        return True, None
    except json.JSONDecodeError as e:
        return False, f"JSON 解析错误: {e}"
    except ValueError as e:
        return False, str(e)


def resolve_template_with_source_url(url: str, token: str | None = None) -> tuple[str, str]:
    clean_url = url.strip().rstrip("/")
    if clean_url.endswith((".jinja", ".json")):
        content = fetch_content(clean_url, token)
        if clean_url.endswith("tokenizer_config.json"):
            data = json.loads(content)
            if "chat_template" not in data:
                raise ValueError("tokenizer_config.json 中未找到 chat_template 字段")
            return data["chat_template"], clean_url
        return content, clean_url

    parsed = parse_model_url(clean_url)
    if not parsed:
        raise ValueError("无法解析 URL，请检查格式")

    platform, owner, repo = parsed
    jinja_url = build_raw_url(platform, owner, repo, "chat_template.jinja")
    try:
        content = fetch_content(jinja_url, token)
        return content, jinja_url
    except requests.HTTPError:
        config_url = build_raw_url(platform, owner, repo, "tokenizer_config.json")
        config_text = fetch_content(config_url, token)
        data = json.loads(config_text)
        if "chat_template" not in data:
            raise ValueError("tokenizer_config.json 中未找到 chat_template 字段")
        return data["chat_template"], config_url


def build_frontend_fetch_script(url: str, token: str | None) -> str:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return f"""
    (async () => {{
        const url = {json.dumps(url)};
        const headers = {json.dumps(headers)};

        async function readText(target) {{
            const response = await fetch(target, {{ headers }});
            if (!response.ok) {{
                throw new Error(`HTTP ${{response.status}} ${{response.statusText}}`);
            }}
            return await response.text();
        }}

        async function readDirect(target) {{
            const text = await readText(target);
            if (target.endsWith("tokenizer_config.json")) {{
                const data = JSON.parse(text);
                if (!data.chat_template) {{
                    throw new Error("tokenizer_config.json 中未找到 chat_template 字段");
                }}
                return {{ content: data.chat_template, sourceUrl: target }};
            }}
            return {{ content: text, sourceUrl: target }};
        }}

        try {{
            if (url.endsWith(".jinja") || url.endsWith(".json")) {{
                return {{ ok: true, ...(await readDirect(url)) }};
            }}

            const parts = {json.dumps(parse_model_url(url) or None)};
            if (!parts) {{
                throw new Error("无法解析 URL，请检查格式");
            }}

            const [platform, owner, repo] = parts;
            const jinjaUrl = platform === "huggingface"
                ? `https://huggingface.co/${{owner}}/${{repo}}/raw/main/chat_template.jinja`
                : `https://modelscope.cn/models/${{owner}}/${{repo}}/resolve/master/chat_template.jinja`;
            const configUrl = platform === "huggingface"
                ? `https://huggingface.co/${{owner}}/${{repo}}/raw/main/tokenizer_config.json`
                : `https://modelscope.cn/models/${{owner}}/${{repo}}/resolve/master/tokenizer_config.json`;

            try {{
                const content = await readText(jinjaUrl);
                return {{ ok: true, content, sourceUrl: jinjaUrl }};
            }} catch (jinjaError) {{
                const text = await readText(configUrl);
                const data = JSON.parse(text);
                if (!data.chat_template) {{
                    throw new Error("tokenizer_config.json 中未找到 chat_template 字段");
                }}
                return {{ ok: true, content: data.chat_template, sourceUrl: configUrl }};
            }}
        }} catch (error) {{
            return {{ ok: false, error: String(error.message || error) }};
        }}
    }})()
    """

st.markdown(
    """
    <div class="app-hero">
        <div class="app-kicker">Jinja Chat Template Lab</div>
        <h1 class="app-title">聊天模板渲染器</h1>
        <p class="app-subtitle">
            粘贴 HuggingFace / ModelScope 模型地址，读取 chat_template.jinja 或 tokenizer_config.json，
            在同一个页面里编辑模板、调试 messages/tools，并即时查看最终渲染文本。
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# Source and options
# ============================================================
with st.container(border=True):
    st.markdown("### 模板来源")
    st.markdown(
        '<p class="caption">支持模型主页、raw 文件、chat_template.jinja 和 tokenizer_config.json。</p>',
        unsafe_allow_html=True,
    )
    col_url, col_token, col_mode, col_btn = st.columns([4.4, 1.8, 1.7, 1.25], vertical_alignment="bottom")
    with col_url:
        model_url = st.text_input(
            "模型网址",
            placeholder="https://huggingface.co/Qwen/Qwen3-... 或 https://modelscope.cn/models/...",
        )
    with col_token:
        hf_token = st.text_input("HuggingFace Token", type="password", placeholder="私有模型可选")
    with col_mode:
        fetch_mode = st.radio(
            "请求方式",
            ["前端 JS", "后端 Python"],
            horizontal=True,
            index=0,
        )
    with col_btn:
        fetch_btn = st.button("读取模板", type="primary", use_container_width=True)
    if st.session_state.template_source_url:
        st.markdown(
            f'<p class="caption">当前模板来源：<code>{st.session_state.template_source_url}</code></p>',
            unsafe_allow_html=True,
        )

with st.container(border=True):
    st.markdown("### 渲染选项")
    col_opt1, col_opt2, col_opt3 = st.columns([1.15, 1.55, 2.3], vertical_alignment="bottom")
    with col_opt1:
        cleanup_ws = st.checkbox("Cleanup template whitespace", value=True)
    with col_opt2:
        add_prompt_clicked = st.button(
            "Add generation prompt",
            key="add_prompt_option",
            help="点击后会将消息 JSON 写入 add_generation_prompt: true。",
            use_container_width=True,
        )
    with col_opt3:
        st.markdown(
            '<p class="caption">左侧编辑 Jinja，中间输入 messages/tools JSON，右侧查看渲染结果。</p>',
            unsafe_allow_html=True,
        )
    if add_prompt_clicked:
        ok, error = apply_add_generation_prompt()
        if ok:
            st.rerun()
        else:
            st.error(error)

# ============================================================
# Fetch logic
# ============================================================
if fetch_btn:
    if not model_url.strip():
        reset_template_state()
        st.session_state.frontend_fetch_pending = False
        st.error("请先输入模型网址")
    elif fetch_mode == "后端 Python":
        st.session_state.frontend_fetch_pending = False
        with st.spinner("正在通过后端 Python 读取模板…"):
            try:
                content, source_url = resolve_template_with_source_url(model_url, hf_token or None)
                st.session_state.jinja_content = content
                st.session_state.template_source_url = source_url
                st.session_state.rendered_result = ""
                st.session_state.render_error = ""
                st.session_state.jinja_editor_version += 1
                st.session_state.result_editor_version += 1
                st.success(f"已读取 {source_url}")
            except ValueError as e:
                reset_template_state()
                st.error(str(e))
            except requests.HTTPError as e:
                reset_template_state()
                st.error(f"HTTP 请求失败: {e}")
            except Exception as e:
                reset_template_state()
                st.error(f"读取失败: {e}")
    else:
        st.session_state.frontend_fetch_key += 1
        st.session_state.frontend_fetch_pending = True
        st.session_state.frontend_fetch_url = model_url
        st.session_state.frontend_fetch_token = hf_token or ""

if st.session_state.frontend_fetch_pending:
    frontend_fetch_result = streamlit_js_eval(
        js_expressions=build_frontend_fetch_script(
            st.session_state.frontend_fetch_url,
            st.session_state.frontend_fetch_token or None,
        ),
        key=f"frontend_fetch_{st.session_state.frontend_fetch_key}",
    )
    if isinstance(frontend_fetch_result, dict) and frontend_fetch_result.get("ok"):
        st.session_state.jinja_content = frontend_fetch_result.get("content", "")
        st.session_state.template_source_url = frontend_fetch_result.get("sourceUrl", "")
        st.session_state.rendered_result = ""
        st.session_state.render_error = ""
        st.session_state.jinja_editor_version += 1
        st.session_state.result_editor_version += 1
        st.session_state.frontend_fetch_pending = False
        st.success(f"已读取 {st.session_state.template_source_url}")
        st.rerun()
    elif isinstance(frontend_fetch_result, dict):
        reset_template_state()
        st.session_state.frontend_fetch_pending = False
        st.error(f"读取失败: {frontend_fetch_result.get('error', '未知错误')}")
        st.rerun()
    else:
        st.info("前端请求已发起，结果返回后页面会自动更新。")


def compute_render_result() -> tuple[str, str | None]:
    jinja_key = f"jinja_editor_{520 if st.session_state.expanded_panel != 'jinja' else 760}_{st.session_state.jinja_editor_version}"
    messages_key = f"messages_editor_{520 if st.session_state.expanded_panel != 'messages' else 760}_{st.session_state.messages_editor_version}"
    jinja_tpl = maybe_format_escaped_template(
        text_value(st.session_state.get(jinja_key)) or st.session_state.jinja_content
    )
    msg_raw = text_value(st.session_state.get(messages_key)) or st.session_state.msg_content

    if not jinja_tpl.strip():
        return "", "请先输入或读取 Jinja 模板"

    try:
        data = json.loads(msg_raw) if msg_raw.strip() else []
        messages = data
        tools = None
        add_generation_prompt = False
        if isinstance(data, dict):
            messages = data.get("messages", [])
            tools = data.get("tools")
            add_generation_prompt = bool(data.get("add_generation_prompt", False))

        result = render_template(
            jinja_tpl,
            messages,
            add_generation_prompt=add_generation_prompt,
            tools=tools,
            cleanup_whitespace=cleanup_ws,
        )
        return result, None
    except json.JSONDecodeError as e:
        return "", f"JSON 解析错误: {e}"
    except Exception as e:
        return "", f"渲染错误: {e}"


def update_render_result() -> None:
    result, error = compute_render_result()
    st.session_state.rendered_result = result
    st.session_state.render_error = error or ""
    st.session_state.result_editor_version += 1


def render_jinja_panel(height: int) -> None:
    with st.container(border=True):
        st.markdown(
            '<div class="panel-title"><h3>Jinja 内容</h3><span>Template</span></div>',
            unsafe_allow_html=True,
        )
        col_copy, col_format, col_expand = st.columns(3)
        with col_copy:
            copy_button("复制", st.session_state.jinja_content, "jinja")
        with col_format:
            format_clicked = st.button("格式化", key=f"format_jinja_{height}", use_container_width=True)
        with col_expand:
            expand_button("jinja")
        edited = code_editor(
            value=st.session_state.jinja_content,
            key=f"jinja_editor_{height}_{st.session_state.jinja_editor_version}",
            language="jinja2",
            height=height,
        )
        if edited != st.session_state.jinja_content:
            st.session_state.jinja_content = edited
            st.session_state.rendered_result = ""
            st.session_state.render_error = ""
            st.session_state.result_editor_version += 1
        if format_clicked:
            st.session_state.jinja_content = format_escaped_template(st.session_state.jinja_content)
            st.session_state.rendered_result = ""
            st.session_state.render_error = ""
            st.session_state.jinja_editor_version += 1
            st.session_state.result_editor_version += 1
            st.rerun()


def render_messages_panel(height: int) -> None:
    with st.container(border=True):
        st.markdown(
            '<div class="panel-title"><h3>消息输入</h3><span>JSON with folding</span></div>',
            unsafe_allow_html=True,
        )
        col_preset, col_copy, col_format, col_expand = st.columns([1.5, 1, 1, 1])
        with col_preset:
            preset = st.selectbox("预设类型", list(PRESETS.keys()), label_visibility="collapsed")
        with col_copy:
            copy_button("复制", st.session_state.msg_content, "messages")
        with col_format:
            format_clicked = st.button("格式化", key=f"format_messages_{height}", use_container_width=True)
        with col_expand:
            expand_button("messages")
        if preset != st.session_state.prev_preset:
            st.session_state.prev_preset = preset
            st.session_state.msg_content = PRESETS[preset] if preset != "自定义" else ""
            st.session_state.rendered_result = ""
            st.session_state.render_error = ""
            st.session_state.messages_editor_version += 1
            st.session_state.result_editor_version += 1
            st.rerun()
        if format_clicked:
            try:
                st.session_state.msg_content = format_json_text(st.session_state.msg_content)
                st.session_state.rendered_result = ""
                st.session_state.render_error = ""
                st.session_state.messages_editor_version += 1
                st.session_state.result_editor_version += 1
                st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"JSON 解析错误: {e}")
        edited = code_editor(
            value=st.session_state.msg_content,
            key=f"messages_editor_{height}_{st.session_state.messages_editor_version}",
            language="json",
            height=height,
        )
        if edited != st.session_state.msg_content:
            st.session_state.msg_content = edited
            st.session_state.rendered_result = ""
            st.session_state.render_error = ""
            st.session_state.result_editor_version += 1


def render_output_panel(height: int) -> None:
    result = st.session_state.rendered_result
    error = st.session_state.render_error
    with st.container(border=True):
        st.markdown(
            '<div class="panel-title"><h3>渲染结果</h3><span>Rendered</span></div>',
            unsafe_allow_html=True,
        )
        col_copy, col_render, col_expand = st.columns(3)
        with col_copy:
            copy_button("复制", result, "result")
        with col_render:
            render_clicked = st.button("渲染", type="primary", key=f"render_now_{height}", use_container_width=True)
        with col_expand:
            expand_button("result")
        if render_clicked:
            update_render_result()
            st.rerun()
        if error:
            if error.startswith("请先"):
                st.info(error)
            else:
                st.error(error)
        elif not result:
            st.info("点击渲染按钮后，会读取上方两个编辑框并生成结果。")
        code_editor(
            value=result,
            key=f"result_editor_{height}_{st.session_state.result_editor_version}",
            language="plain_text",
            height=height,
            readonly=True,
            auto_update=False,
        )

# ============================================================
# Three-column panel
# ============================================================
expanded = st.session_state.expanded_panel

if expanded == "jinja":
    render_jinja_panel(760)
elif expanded == "messages":
    render_messages_panel(760)
elif expanded == "result":
    render_output_panel(760)
else:
    col1, col2 = st.columns(2)
    with col1:
        render_jinja_panel(520)
    with col2:
        render_messages_panel(520)
    render_output_panel(420)
