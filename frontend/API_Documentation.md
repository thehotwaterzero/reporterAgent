# AI 记者助手后端 API 文档

## 基本信息

**基础 URL:** `http://localhost:5000`

**Content-Type:** `application/json`

**支持的HTTP方法:** `GET`, `POST`

---

## 接口列表

### 1. 获取所有对话会话

**接口描述:** 获取系统中所有的对话会话及其详细信息

**URL:** `/dialogues`

**方法:** `GET`

**请求参数:** 无

#### 响应格式

**成功响应 (200 OK):**

```json
{
  "1": {
    "id": 1,
    "created_at": "2025-01-15T10:30:00",
    "updated_at": "2025-01-15T10:45:00",
    "is_finished": false,
    "draft": "这是一个关于环保的报告草稿...",
    "qas": [
      {
        "id": 1,
        "question": "你想了解什么主题？",
        "answer": "我想了解环保相关的内容",
        "aim": "信息收集",
        "emotion": "neutral",
        "progress": "初始阶段",
        "created_at": "2025-01-15T10:30:00",
        "updated_at": "2025-01-15T10:30:00",
        "dubious": [
          {
            "id": 1,
            "snippet": "具体环保领域需要进一步确认"
          }
        ]
      }
    ]
  },
  "2": {
    "id": 2,
    "created_at": "2025-01-15T11:00:00",
    "updated_at": "2025-01-15T11:20:00",
    "is_finished": true,
    "draft": "这是另一个完成的报告...",
    "qas": []
  }
}
```

**响应字段说明:**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | integer | 会话唯一标识符 |
| `created_at` | string | 会话创建时间 (ISO 8601格式) |
| `updated_at` | string | 会话最后更新时间 (ISO 8601格式) |
| `is_finished` | boolean | 会话是否已完成 |
| `draft` | string | 当前生成的报告草稿内容 |
| `qas` | array | 该会话中的问答记录列表 |

**QA记录字段说明:**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | integer | 问答记录唯一标识符 |
| `question` | string | AI提出的问题 |
| `answer` | string | 用户的回答 |
| `aim` | string | 问题的目的/意图 |
| `emotion` | string | 检测到的用户情绪 |
| `progress` | string | 当前对话进度描述 |
| `created_at` | string | 记录创建时间 |
| `updated_at` | string | 记录更新时间 |
| `dubious` | array | 可疑/需要核查的信息片段 |

**可疑信息字段说明:**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | integer | 可疑信息唯一标识符 |
| `snippet` | string | 可疑信息的文本片段 |

---

### 2. 开始新对话

**接口描述:** 开始一个新的对话会话，AI会基于初始输入开始提问

**URL:** `/start`

**方法:** `POST`

**请求头:** 
- `Content-Type: application/json`
- `Accept: text/event-stream` (用于接收流式响应)

#### 请求参数

```json
{
  "input": "张小懿，男，美的集团副总裁兼首席数字官（CDO），掌舵集团数字化转型十余年，推动从“632”到AI智能体的全面升级，现任职于集团最高数字化决策层。"
}
```

**请求字段说明:**

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `input` | string | 是 | 初始输入，描述受访者的基础信息 |

#### 响应格式

**成功响应 (200 OK):**

这是一个**流式响应**接口，使用 Server-Sent Events (SSE) 格式。客户端需要监听 `text/event-stream` 数据流。

**流式响应示例:**

```
data: {"type": "emotion", "content": "negative", "data": {"emotion": "negative", "dubious": [], "process": null, "aim": null, "question": null, "is_finished": false, "draft": null}}

data: {"type": "dubious", "content": "发现可疑内容: 0项", "data": {"emotion": "negative", "dubious": [], "process": null, "aim": null, "question": null, "is_finished": false, "draft": null}}

data: {"type": "process", "content": "序章 100%（年代+环境+关键影响因素完整覆盖）", "data": {"emotion": "negative", "dubious": [], "process": "序章 100%（年代+环境+关键影响因素完整覆盖）", "aim": null, "question": null, "is_finished": 0, "draft": null}}

data: {"type": "is_finished", "content": "0", "data": {"emotion": "negative", "dubious": [], "process": "序章 100%（年代+环境+关键影响因素完整覆盖）", "aim": null, "question": null, "is_finished": 0, "draft": null}}

data: {"type": "aim", "content": "自然过渡到时代篇，将个人经历与国家叙事关联", "data": {"emotion": "negative", "dubious": [], "process": "序章 100%（年代+环境+关键影响因素完整覆盖）", "aim": "自然过渡到时代篇，将个人经历与国家叙事关联", "question": null, "is_finished": 0, "draft": null}}

data: {"type": "question", "content": "您提到把美的流程拆解成632个节点，这让我想到中国的制造业升级。在您职业生涯中，有没有某个特定的国家政策或社会变革，让您深刻感受到数字化浪潮的袭来？", "data": {"emotion": "negative", "dubious": [], "process": "序章 100%（年代+环境+关键影响因素完整覆盖）", "aim": "自然过渡到时代篇，将个人经历与国家叙事关联", "question": "您提到把美的流程拆解成632个节点，这让我想到中国的制造业升级。在您职业生涯中，有没有某个特定的国家政策或社会变革，让您深刻感受到数字化浪潮的袭来？", "is_finished": 0, "draft": null}}

data: {"type": "final", "content": "✅ 处理完成", "data": {"emotion": "negative", "dubious": [], "process": "序章 100%（年代+环境+关键影响因素完整覆盖）", "aim": "自然过渡到时代篇，将个人经历与国家叙事关联", "question": "您提到把美的流程拆解成632个节点，这让我想到中国的制造业升级。在您职业生涯中，有没有某个特定的国家政策或社会变革，让您深刻感受到数字化浪潮的袭来？", "is_finished": 0, "draft": null}}
```

**流式数据类型说明:**

| 类型 | 字段 | 说明 |
|------|------|------|
| string | `type` | 当前处理进度和状态信息 |
| string | `content` | 提示信息 |
| string | `data` | 当前阶段的处理结果 |

**type字段内容说明:**

| 字段值 | 说明 |
|---|---|
| `emotion` | data中的`emotion`字段赋值完成 |
| `dubious` | data中的`dubious`字段赋值完成 |
| `process` | data中的`process`字段赋值完成 |
| `aim` | data中的`aim`字段赋值完成 |
| `question` | data中的`question`字段赋值完成 |
| `is_finished` | data中的`is_finished`字段赋值完成 |
| `draft` | data中的`draft`字段赋值完成 |


**data字段内容说明:**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `emotion` | string | 检测到的用户情绪状态 |
| `dubious` | array | 可疑或需要核查的信息列表 |
| `process` | string | 当前进度描述 |
| `aim` | string/null | 当前阶段的目标 |
| `question` | string/null | 生成的问题内容 |
| `is_finished` | integer | 会话完成状态 (0=未完成, 1=已完成) |
| `draft` | string/null | 当前生成的草稿内容 |

**错误响应 (400 Bad Request):**

```json
{
  "error": "Initial input is required"
}
```

---

### 3. 继续对话

**接口描述:** 在现有会话中继续对话，回答AI的问题

**URL:** `/continue`

**方法:** `POST`

**请求头:**
- `Content-Type: application/json`
- `Accept: text/event-stream` (用于接收流式响应)

#### 请求参数

```json
{
  "session_id": 123,
  "input": "主要面向企业决策者和技术专家"
}
```

**请求字段说明:**

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `session_id` | integer | 是 | 要继续的会话ID |
| `input` | string | 是 | 用户对AI问题的回答 |

#### 响应格式

**成功响应 (200 OK):**

同样是**流式响应**，格式与 `/start` 接口相同。

**流式响应示例:**

参考 `/start` 接口的响应格式，包含相同的数据结构和类型。

**错误响应 (400 Bad Request):**

```json
{
  "error": "Session ID and user input are required"
}
```

---

## 错误码说明

| HTTP状态码 | 错误类型 | 说明 |
|------------|----------|------|
| 200 | 成功 | 请求成功处理 |
| 400 | 请求错误 | 缺少必需参数或参数格式不正确 |
| 404 | 未找到 | 请求的会话不存在 |
| 500 | 服务器错误 | 服务器内部错误 |

---

## 注意事项

1. **流式响应处理**: `/start` 和 `/continue` 接口使用 Server-Sent Events，需要正确处理流式数据
2. **会话管理**: 需要妥善保存和管理 `session_id`，用于后续的对话继续
3. **错误处理**: 建议为所有接口调用添加适当的错误处理逻辑
4. **超时处理**: 对于长时间运行的对话，建议设置合适的超时时间
5. **数据缓存**: 可以考虑缓存历史对话数据以提升用户体验

---

**文档版本:** v1.0  
**最后更新:** 2025年1月15日  
**联系方式:** [开发团队邮箱]