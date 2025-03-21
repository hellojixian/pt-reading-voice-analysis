# PT阅读语音分析应用 API文档

## 概述

本文档详细说明PT阅读语音分析应用的服务器API。这些API提供了语音转文本、文本转语音、聊天功能以及基于OpenAI Assistant的高级对话功能。

## 基础URL

所有API路径均基于以下基础URL:
```
http://localhost:8000
```

## API端点

### 健康检查

#### 获取系统健康状态

```
GET /api/health
```

检查服务是否正常运行。

**响应示例:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "message": "服务正常运行"
}
```

### 语音服务

#### 语音转文本

```
POST /api/speech-to-text
```

将音频文件转换为文本。

**请求参数:**
- `audio`: 音频文件（表单数据）

**支持的音频格式:**
- MP3 (.mp3)
- WAV (.wav)
- OGG (.ogg)
- WebM (.webm)

**响应示例:**
```json
{
  "text": "这是从音频中转录的文本内容"
}
```

#### 文本转语音

```
POST /api/text-to-speech
```

将文本转换为语音并返回音频URL。

**请求参数:**
- `text`: 要转换为语音的文本内容
- `voice` (可选): 语音类型，默认为"alloy"

**可用的语音类型:**
- alloy
- echo
- fable
- onyx
- nova
- shimmer

**请求示例:**
```json
{
  "text": "你好，世界！",
  "voice": "nova"
}
```

**响应示例:**
```json
{
  "audio_url": "/api/audio/abc123.mp3"
}
```

#### 获取音频文件

```
GET /api/audio/{filename}
```

获取由文本转语音功能生成的音频文件。

**路径参数:**
- `filename`: 音频文件名

**响应:**
- 音频文件（MIME类型: audio/mpeg）

### 聊天服务

#### 发送聊天消息

```
POST /api/chat
```

发送消息并获取AI回复。

**请求参数:**
- `message`: 用户消息内容
- `language` (可选): 语言代码，"en"或"zh"，默认为"en"

**请求示例:**
```json
{
  "message": "你好，我是谁？",
  "language": "zh"
}
```

**响应示例:**
```json
{
  "text": "你好！你是一个用户，我是AI助手。",
  "audio_url": "/api/audio/abc123.mp3"
}
```

#### 重置聊天历史

```
POST /api/chat/reset
```

清除当前的聊天历史记录。

**响应示例:**
```json
{
  "status": "success",
  "message": "聊天历史已重置"
}
```

### Assistant服务

Assistant服务基于OpenAI的Assistant API，提供更高级的对话功能，包括图书推荐、图书搜索等。

#### 发送Assistant聊天消息

```
POST /api/assistant-chat
```

发送消息到OpenAI Assistant并获取回复。

**请求参数:**
- `message`: 用户消息内容
- `language` (可选): 语言代码，"en"或"zh"，默认为"en"

**请求示例:**
```json
{
  "message": "请推荐一些冒险类的书籍",
  "language": "zh"
}
```

**响应示例:**
```json
{
  "text": "以下是一些适合你的冒险类书籍推荐...",
  "audio_url": "/api/audio/abc123.mp3",
  "function_results": [
    {
      "name": "recommend_books",
      "arguments": {
        "user_interests": "冒险小说"
      },
      "result": {
        "status": "success",
        "recommended_books": [
          {
            "book_id": "12345",
            "book_title": "海底两万里",
            "reason": "这是一本经典的冒险小说"
          }
        ]
      }
    }
  ]
}
```

#### 流式Assistant聊天

```
GET /api/assistant-chat-stream?message={message}&language={language}
```

以服务器发送事件(SSE)流的形式获取Assistant的响应，适用于实时更新UI。

**查询参数:**
- `message`: 用户消息内容（URL编码）
- `language` (可选): 语言代码，"en"或"zh"，默认为"en"

**响应:**
服务器发送事件(SSE)流，包含以下事件类型:
- `status`: 处理状态更新
- `progress`: 进度更新（例如函数调用过程）
- `complete`: 完成的响应
- `error`: 错误信息

**事件示例:**
```
event: status
data: {"status": "Thinking..."}

event: progress
data: {"status": "Processing book_recommendation...", "progress": {"type": "book_recommendation", "icon": "📚"}}

event: complete
data: {"text": "以下是一些适合你的冒险类书籍推荐...", "audio_url": "/api/audio/abc123.mp3", "function_results": [...]}
```

## 助手功能

Assistant API支持以下特殊功能:

### 图书推荐

基于用户兴趣推荐图书。当用户询问图书推荐时，系统会分析用户兴趣并推荐相关图书。

### 图书搜索

根据书名搜索图书。当用户提及特定书名时，系统会搜索匹配的图书并提供信息。

### 图书内容获取

获取特定图书的详细内容。当用户想讨论某本书时，系统会获取该书的内容并能回答相关问题。

## 错误处理

所有API端点在发生错误时返回标准JSON错误响应:

```json
{
  "error": "错误消息描述"
}
```

常见HTTP状态码:
- 200 OK: 请求成功
- 400 Bad Request: 请求参数无效
- 500 Internal Server Error: 服务器内部错误

## 内容审核

所有文本内容（包括用户输入和AI回复）都会经过内容审核，确保内容适合儿童。如果检测到不适当内容，系统会返回友好的警告消息而不是原始响应:

```json
{
  "text": "这个话题不适合你的年龄...",
  "is_warning": true,
  "audio_url": "/api/audio/abc123.mp3"
}
