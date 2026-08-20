# JobPilot

JobPilot是一个基于DeepSeek API的简历与岗位匹配分析应用。它可解析TXT、Markdown、PDF和DOCX简历，提取JD结构，并输出加权匹配分数、关键词缺口、能力差距和可执行修改建议。

## 已实现能力

- DeepSeek API调用与固定Prompt
- JD结构化提取
- 简历/JD匹配分析与0-100分输出
- TXT、Markdown、PDF、DOCX简历文本解析
- 意图路由与多轮用户画像收集
- 本地JSON用户画像记忆
- JSON字段和分数范围校验
- Streamlit Web界面、结果分栏与多轮追问
- JD文字输入与图片输入可同时使用，支持截图上传、剪贴板粘贴及中文OCR校对
- Markdown和JSON分析报告导出
- 基于原始简历与JD生成定制简历，并导出Word和PDF
- 评分后由用户选择是否一键生成JD定制简历
- 支持对中文或英文成稿进行多轮调整，并同步刷新Word/PDF
- 中文和英文成稿均支持一键压缩为美观的一页版
- 将中文简历翻译并本地化为无照片、ATS友好的英文简历
- 双工作区响应式界面与统一视觉设计

本项目没有实现向量数据库或RAG知识库。“本地用户画像记忆”不等同于知识库。

## 安装

```powershell
python -m pip install -r requirements.txt
$env:DEEPSEEK_API_KEY="你的密钥"
```

## 使用

运行多轮对话：

```powershell
python chat.py
```

运行Web应用：

```powershell
streamlit run streamlit_app.py
```

代码中分析简历文件：

```python
from agents.career_agent import CareerAgent
from utils.llm import create_client

agent = CareerAgent(create_client())
result = agent.analyze_resume_file("resume.pdf", "岗位JD文本")
```

## 测试

离线测试使用模拟模型响应，不调用DeepSeek API：

```powershell
python -m unittest discover -s tests -v
```

## 部署到Streamlit Community Cloud

1. 将项目推送到你拥有管理员权限的GitHub仓库。
2. 登录`share.streamlit.io`并连接GitHub。
3. 创建应用，选择仓库、分支及入口文件`streamlit_app.py`。
4. 在Advanced settings的Secrets中配置：

```toml
DEEPSEEK_API_KEY = "你的DeepSeek密钥"
```

5. 选择与本地兼容的Python版本并部署。

不要提交`.streamlit/secrets.toml`、`memory/user_profile.json`或任何真实API密钥。上传的简历和JD会发送至DeepSeek API完成分析，公开使用前应提示用户移除不必要的敏感信息。

## 输出边界

匹配分数来自模型基于输入证据的判断，只用于辅助筛选，不代表招聘结果。系统把没有证据的要求标记为能力缺口或未知项，并要求匹配证据来自用户简历或画像。
