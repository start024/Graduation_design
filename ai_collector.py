import os
import json
import time
import datetime
from google import genai
from app import app
from models import db, SecurityEvent

# 1. 代理配置（确保端口与 Clash Verge 一致）
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7897"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"

# 2. 初始化客户端 (请替换为你的有效 API Key)
client = genai.Client(api_key="AIzaSyDqZQh7GeM6KsKOHx5ZzcZA9f5jQ-_sae0")

def smart_fetch(topic):
    print(f"\n--- 正在检索: {topic} ---")
    
    prompt = f"""
    作为安全专家，请列出10条关于 {topic} 的真实或典型安全事件。
    返回 JSON 数组格式，包含字段：title, content, category, risk_level。
    category 必须在 [Prompt Injection, Model Jailbreak, Data Exposure, Supply Chain, Others] 中选择。
    仅返回纯 JSON，不要包含任何 Markdown 格式。
    """
    
    try:
        # 调用模型
        response = client.models.generate_content(
            model="gemini-2.5-flash", # 1.5-flash 通常比 2.0 免费额度更稳
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        
        # 安全性检查：确保 response 和 response.text 存在
        if not response or not response.text:
            print(f"API 返回内容为空，可能是额度已耗尽或网络中断。")
            return

        print("收到响应，正在解析...")
        events = json.loads(response.text.strip())
        
        # 确保解析出来的是列表
        if not isinstance(events, list):
            print("返回的 JSON 格式不是列表。")
            return

        with app.app_context():
            added_count = 0
            for item in events:
                # 再次检查 key 是否存在，防止字段缺失报错
                title = item.get('title')
                if not title: continue
                
                if not SecurityEvent.query.filter_by(title=title).first():
                    event = SecurityEvent(
                        title=title,
                        source="Gemini-AI",
                        category=item.get('category', 'Others'),
                        content=item.get('content', '无详细描述'),
                        risk_level=item.get('risk_level', '中'),
                        publish_time=datetime.datetime.now()
                    )
                    db.session.add(event)
                    added_count += 1
            db.session.commit()
            print(f"成功入库 {added_count} 条数据！")
            
    except json.JSONDecodeError:
        print("JSON 解析失败，AI 返回的内容格式不正确。")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    # 第一批测试话题
    test_topics = [
    #"LLM Prompt Injection attacks 2025",
    #"Generative AI Data Leaks",
    #"AI Jailbreak examples",

    # 1. 强化弱势类别：模型窃取与反向工程 (对应 LLM10: Model Theft)
    "Model extraction attacks on proprietary LLMs",
    "Reverse engineering AI model parameters incidents",
    "Stealing fine-tuned weights from cloud-based AI",
    "Side-channel attacks on LLM inference infrastructure",

    # 2. 强化弱势类别：输出处理与插件安全 (对应 LLM02 & LLM07)
    "XSS vulnerabilities via LLM output rendering",
    "Insecure Plugin implementation in LLM agents",
    "Cross-site scripting attacks via AI-generated Markdown",
    "Unauthorized tool execution by LLM-based assistants",

    # 3. 2025-2026 最新趋势：多模态与物理层攻击
    "Vulnerabilities in Vision-Language Models (VLM) 2026",
    "Adversarial image injection in GPT-4o and Gemini",
    "Malicious audio prompt injection in voice-AI",
    "Physical world adversarial attacks on multimodal AI",

    # 4. 自动化智能体 (AI Agents) 与 RAG 安全
    "Privilege escalation in autonomous AI agent workflows",
    "Indirect prompt injection via RAG vector databases",
    "Poisoning attacks on RAG-based knowledge retrieval",
    "Confused deputy attacks in multi-agent AI systems",

    # 5. 基础设施与供应链深度安全 (对应 LLM05)
    "Dependency attacks on AI-specific libraries (LangChain/LlamaIndex)",
    "Hugging Face Hub model repository hijacking cases",
    "GPU memory exhaustion attacks on LLM API endpoints",
    "Supply chain vulnerabilities in pre-trained model weights"

    # 核心攻击类
    "Direct Prompt Injection examples 2025", "Indirect Prompt Injection in RAG",
    "LLM Jailbreak through multi-step reasoning", "Advanced jailbreak via role-playing",

    # 提示注入类
    "Prompt Injection vulnerabilities in GPT-4", "Indirect prompt injection cases 2025",
    "Prompt leaking security incidents", "System prompt bypass techniques",
       
    # 越狱类
    "LLM Jailbreak patterns 2023-2025", "Adversarial attacks on Llama-3",
    "Universal jailbreak strings for generative AI", "Role-play attack security risks", 

    # 数据泄露与隐私
    "Training data extraction attacks on LLM", "Personal Identifiable Information leak in AI",
    "Membership inference attacks on generative models", "PII exposure in RAG systems",
    "Sensitive Data Leakage in ChatGPT history", "PII extraction attacks on LLMs",
    "Membership Inference Attacks on Generative AI", "Training data regurgitation incidents",

    # 供应链与工具安全
    "Vulnerabilities in LangChain Framework", "Malicious GPT Store assistants",
    "LlamaIndex security flaws", "Dependency attacks in AI pipelines",
    "Supply Chain attacks on Hugging Face models", "Vulnerabilities in LangChain agents",
    "Insecure Plugin implementation in LLMs", "Poisoning attacks on fine-tuning datasets",

    # 企业级事件
    "Microsoft Copilot security concerns", "OpenAI data breach incidents",

    # 1. 模型窃取与反向工程 (对应 LLM10: Model Theft)
    "Model extraction attacks on proprietary LLMs",
    "Reverse engineering AI model parameters incidents",
    "Side-channel attacks on LLM inference hardware",
    "IP theft of custom fine-tuned GPT models",
    
    # 2. 多模态 AI 安全 (图像/语音/视频交叉攻击)
    "Vulnerabilities in Vision-Language Models (VLM) 2025",
    "Adversarial image attacks on Multimodal LLMs",
    "Malicious audio injection in voice-activated AI",
    "Security risks in text-to-video generation models",
    
    # 3. AI Agent (智能体) 与自动化工作流安全
    "Privilege escalation in autonomous AI agents",
    "Malicious tool use by compromised AI assistants",
    "Chain-of-thought manipulation in AI workflows",
    "Cross-application prompt injection via AI agents",
    
    # 4. 基础设施、文档解析与存储安全
    "Prompt injection via PDF and Word document parsing",
    "Security vulnerabilities in Vector Databases like Milvus or Weaviate",
    "Insecure API key storage in AI development environments",
    "GPU memory exhaustion attacks on LLM servers",
    
    # 5. 社会工程学、滥用与恶意软件
    "Deepfake phishing campaigns powered by LLMs",
    "Automated disinformation generation using Generative AI",
    "AI-generated malware and polymorphic code incidents",
    "Social engineering via personalized LLM chatbots"
    ]
    
    for t in test_topics:
        smart_fetch(t)
        # 免费层级建议每分钟请求不超过 2-3 次，增加延迟
        print("等待 20 秒后执行下一个话题...")
        time.sleep(20)