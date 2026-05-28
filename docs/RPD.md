# Jinja Render — 产品需求文档 (RPD)

## 1. 概述

**项目名称**: Jinja Render  
**目标**: 提供一个在线工具，让用户输入 HuggingFace / ModelScope 模型链接，自动获取其 `chat_template.jinja` 或 `tokenizer_config.json` 中的 `chat_template` 字段，并在三栏 UI 中编辑模板、输入消息、预览渲染结果。

---

## 2. 功能需求

### 2.1 模型 URL 输入与自动读取

| 字段 | 说明 |
|------|------|
| 输入框 | 用户粘贴 HuggingFace 或 ModelScope 的模型主页 URL |
| 自动识别 | 解析 URL，判断来源平台，提取 owner 和 model name |
| 读取策略 | 1. 优先请求 `chat_template.jinja` 文件内容<br>2. 若 404，则请求 `tokenizer_config.json`，解析其中的 `chat_template` 字段 |
| 读取按钮 | 「读取模板」按钮触发请求，结果填充到第一栏（Jinja 内容） |

**支持示例 URL**:

- `https://huggingface.co/openbmb/MiniCPM5-1B/`
- `https://huggingface.co/Qwen/Qwen2.5-7B-Instruct`
- `https://huggingface.co/Qwen/Qwen3.5-9B/raw/main/chat_template.jinja`
- `https://modelscope.cn/models/NemoStation/Marlin-2B`
- `https://modelscope.cn/models/NemoStation/Marlin-2B/resolve/master/chat_template.jinja`

**请求地址拼接规则**:

- HuggingFace: `https://huggingface.co/{owner}/{repo}/raw/main/{filename}`
- ModelScope: `https://modelscope.cn/models/{owner}/{repo}/resolve/master/{filename}`

### 2.2 三栏布局

```
┌─────────────────────────────────────────────────────┐
│  [URL 输入框]  [读取模板]                           │
│  ☐ Add generation prompt  ☐ Cleanup whitespace      │
│  [HuggingFace Token 输入]                           │
├──────────┬──────────────────┬───────────────────────┤
│ 第一栏   │ 第二栏           │ 第三栏                │
│ Jinja 内 │ 消息输入         │ 渲染结果              │
│ 容       │ (预填充+分类)    │ (实时渲染)            │
│          │                  │                       │
│ [格式化] │                  │                       │
└──────────┴──────────────────┴───────────────────────┘
```

#### 第一栏 — Jinja 内容

- 文本编辑区，支持直接粘贴/编辑 Jinja 模板
- 工具栏按钮：「格式化」 — 将选中文本或全文中的 `\n` 字面量替换为真实换行符（针对从 HuggingFace 等网站复制过来的一行模板）
- 从 URL 读取后自动填充到此区域

#### 第二栏 — 消息输入

- 内容类型：字典/JSON 格式的消息列表（按 Jinja `messages` 和 `tools` 变量约定）
- **预设分类下拉菜单**（用户可选择切换不同类型）：
  1. **纯消息** — 预设一组普通对话消息
  2. **消息 + 工具** — 预设包含 tools 定义的消息
  3. **多模态示例** — 预设包含 image 等字段的多模态消息
  4. **自定义** — 空白，用户自行编辑
- 支持手动编辑 JSON
- 提供基础校验（JSON 格式是否合法）

#### 第三栏 — 渲染结果

- 调用 Jinja 渲染引擎，实时或点击「渲染」后展示结果
- 显示渲染后的文本内容（只读）
- 若渲染出错，显示错误信息（红色提示）

### 2.3 可选开关与配置

| 选项 | 类型 | 默认 | 说明 |
|------|------|------|------|
| Add generation prompt | checkbox | 否 | 渲染时在末尾附加 generation prompt |
| Cleanup template whitespace | checkbox | 是 | 渲染前对模板做空白清理 |
| HuggingFace Token | input | 空 | 私有模型需要传入 HF Token（仅 HF 请求时使用） |

### 2.4 交互细节

1. **URL 读取**：点击「读取模板」后显示 loading 状态；成功则填充第一栏，失败则提示错误
2. **自动渲染**：第一栏/第二栏内容变化后自动触发重新渲染（带防抖）
3. **格式化按钮**：支持将 `\\n` 或 `\n` 字面字符串替换为实际换行
4. **分类切换**：切换第二栏预设时，保留用户已编辑内容（通过确认弹窗）或替换

---

## 3. 非功能需求

- 纯 Python 实现，基于 Streamlit 单进程运行
- 使用 `jinja2` 库进行服务端渲染
- 响应式布局（Streamlit 默认支持）
- 历史 URL 记录（`st.session_state`）

---

## 4. 技术选型

| 模块 | 方案 |
|------|------|
| 框架 | Streamlit（Python） |
| 模板渲染 | Python `jinja2` 库 |
| HTTP 请求 | `requests` 库 |
| 模型 URL 解析 | 正则 + `urllib.parse` |

---

## 5. 消息预设数据

### 5.1 纯消息

```json
[
  {"role": "system", "content": "You are a helpful assistant."},
  {"role": "user", "content": "Hello!"},
  {"role": "assistant", "content": "Hi! How can I help you?"},
  {"role": "user", "content": "What is the capital of France?"}
]
```

### 5.2 消息 + 工具

```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant with access to tools."},
    {"role": "user", "content": "What's the weather like in Beijing?"},
    {"role": "assistant", "content": "", "tool_calls": [{"type": "function", "function": {"name": "get_weather", "arguments": "{\"location\": \"Beijing\"}"}}]},
    {"role": "tool", "content": "{\"temperature\": 22, \"condition\": \"sunny\"}", "name": "get_weather"},
    {"role": "assistant", "content": "The weather in Beijing is currently 22°C and sunny."}
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
            "location": {"type": "string", "description": "City name"}
          },
          "required": ["location"]
        }
      }
    }
  ]
}
```

### 5.3 多模态示例

```json
[
  {"role": "user", "content": [{"type": "image", "url": "https://example.com/image.jpg"}, {"type": "text", "text": "Describe this image"}]},
  {"role": "assistant", "content": "This is a beautiful landscape with mountains."}
]
```

---

## 6. 约束与边界情况

- `chat_template.jinja` 可能不存在 → 静默回退到 `tokenizer_config.json`
- `tokenizer_config.json` 中可能无 `chat_template` 字段 → 提示用户手动粘贴
- ModelScope 国内访问可能更快，HuggingFace 需科学上网
- 某些模型的 chat_template 包含 `add_generation_prompt` / `eos_token` 等变量，需在渲染时注入
- 模板内容可能含中文注释或特殊字符，需 UTF-8 正确处理
