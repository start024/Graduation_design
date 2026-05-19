import os
import requests
import datetime
import time
from app import app
from models import db, SecurityEvent

# --- 用户配置区 ---
# 请将你邮箱里收到的 API Key 填在这个字符串里
NVD_API_KEY = "xxxxx"

# 1. 代理配置（如果在校园网或需要 Clash 才能连外网访问 NIST，请开启；如果不需要请注释掉）
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7897"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"

def fetch_nvd_llm_vulnerabilities():
    print(f"[{datetime.datetime.now()}] [START] 启动 NVD 权威漏洞库同步程序...")
    
    # NVD 官方 2.0 API 接口
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    headers = {}
    if NVD_API_KEY != "PLEASE_FILL_IN_YOUR_API_KEY_HERE":
        # 如果填写了 API Key，NVD 会大幅放宽限流频率 (每 30 秒 50 次请求)
        headers["apiKey"] = NVD_API_KEY
        print("SUCCESS: 已加载 NVD API Key 获取高优先级访问权。")
    else:
        print("WARNING: 未配置 API Key，正在使用匿名限流模式（每 30 秒 5 次）。为了稳定运行，请务必填入 Key。")

    # 核心搜索关键词：覆盖框架、模型、特定攻击类型和基础设施
    keywords = [
        # 1. 基础设施与推理加速引擎 (最容易出 CVE 的地方)
        "vLLM", "DeepSpeed", "FlashAttention", "TensorRT", "OpenVINO", 
        "Hugging Face Safetensors", "GGUF", "AWQ", "BitsAndBytes", 
        "CUDA Graph", "NCCL", "Triton Compiler",

        # 2. 向量数据库与 RAG 存储 (LLM 的“外挂存储”漏洞)
        "Milvus", "Weaviate", "Pinecone", "ChromaDB", "Qdrant", 
        "Faiss", "Elasticsearch AI", "LanceDB", "Vector Collision",

        # 3. 智能体与自动化框架 (Agent 权限越权)
        "CrewAI", "Microsoft AutoGen", "BabyAGI", "Semantic Kernel", 
        "Tool Use", "Function Calling", "Agent Sandbox", "Insecure Tool Execution",

        # 4. 新型攻击向量描述词 (NVD 常用术语)
        "Prompt Hijacking", "Indirect Injection", "Tainted Input", 
        "Side-channel Inference", "Token Leakage", "Weight Reconstruction",
        "Denial of Wallet", "Model Inversion", "Adversarial Suffix",

        # 5. 跨模态与多媒体组件 (针对 GPT-4o, Gemini)
        "VLM", "Vision-Language", "Multimodal Safety", "Audio Injection", 
        "OCR Injection", "CLIP", "Stable Diffusion", "Whisper",

        # 6. 国产/开源生态 (补充 NVD 中可能出现的)
        "DeepSeek", "Qwen", "Zhipu AI", "Baichuan", "Yi-34B"

        # 通用与模型类
        "LLM", "Large Language Model", "Generative AI", "Transformer Model", 
        "GPT-4", "Llama", "Mistral AI", "Anthropic", "OpenAI",
        
        # 框架与库
        "HuggingFace", "Transformers library", "LangChain", "LlamaIndex", 
        "PyTorch", "TensorFlow", "Keras", "ModelHub", "AutoGPT",
        
        # 攻击类型 (核心安全词)
        "Prompt Injection", "Prompt Leaking", "Jailbreak", "Model Jailbreak",
        "Adversarial Attack", "Data Poisoning", "Training Data Poisoning",
        "Model Extraction", "Membership Inference", "Insecure Output Handling",
        
        # 应用与组件
        "AI Agent", "Vector Database", "RAG", "Retrieval-Augmented Generation",
        "Ollama", "vLLM", "Triton Inference", "NVIDIA Triton", 
        "MLflow", "Weights & Biases", "Tensors"
    ]
    
    total_added = 0
    
    with app.app_context():
        for keyword in keywords:
            print(f"\n[SEARCH] 正在检索关键词: '{keyword}' 的 CVE 漏洞...")
            
            # 构造查询参数 (keywordSearch 可以在 CVE 的描述里搜词)
            params = {
                "keywordSearch": keyword,
                # "resultsPerPage": 20 # 默认 20，如果用 API key 可以拉更多
            }

            try:
                # 即使有 API Key 也加上超时时间，NVD 比较慢
                response = requests.get(url, headers=headers, params=params, timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    vulnerabilities = data.get("vulnerabilities", [])
                    
                    if not vulnerabilities:
                        print(f"  没有找到关于 '{keyword}' 的漏洞。")
                        continue
                        
                    print(f"  找到 {len(vulnerabilities)} 个关联漏洞，正在入库...")
                    
                    count = 0
                    for item in vulnerabilities:
                        cve_data = item.get("cve", {})
                        cve_id = cve_data.get("id", "Unknown-CVE")
                        
                        # 获取英文描述，NVD 的 descriptions 是一个数组
                        descriptions = cve_data.get("descriptions", [])
                        desc_text = "N/A"
                        for d in descriptions:
                            if d.get("lang") == "en":
                                desc_text = d.get("value")
                                break
                        
                        # 我们把编号拼到标题里，看起来非常专业
                        full_title = f"[{cve_id}] {keyword} 漏洞"
                        
                        # 获取高危/中危评分结构 (CVSS Metrics)
                        metrics = cve_data.get("metrics", {})
                        # 这里为了演示简单，我们如果查到它有 V3 评分标准，那就是一条完整的告警
                        risk_level = "中"
                        cvss_metrics = metrics.get('cvssMetricV31') or metrics.get('cvssMetricV30')
                        if cvss_metrics and len(cvss_metrics) > 0:
                            base_score = cvss_metrics[0].get('cvssData', {}).get('baseScore', 5.0)
                            if base_score >= 7.0:
                                risk_level = "高"
                            elif base_score < 4.0:
                                risk_level = "低"
                        
                        # 查重：数据库里是不是已经收录了这个 CVE？
                        if not SecurityEvent.query.filter_by(title=full_title).first():
                            event = SecurityEvent(
                                title=full_title,
                                source="NVD (National Vulnerability Database)",
                                content=desc_text,
                                category="Others", # 待后续接入分类器自动打标
                                risk_level=risk_level,
                                publish_time=datetime.datetime.now()
                            )
                            db.session.add(event)
                            count += 1
                            total_added += 1
                    
                    db.session.commit()
                    print(f"  入库成功，本次抓取新增 {count} 条！")
                    
                else:
                    print(f"WARNING: 请求 NVD 失败，状态码: {response.status_code}。可能触发限流。")
                
            except Exception as e:
                print(f"ERROR: 检索 '{keyword}' 时发生网络错误: {e}")
            
            # API 礼仪：NVD 规定哪怕有 key，也最好控制请求速率
            print("WAIT: 强制休眠 6 秒，防止被 NIST 封锁 API Key...")
            time.sleep(6)

    print(f"\nDONE: 权威数据采集结束！系统总共新增 {total_added} 条国家漏洞记录。")

if __name__ == "__main__":
    fetch_nvd_llm_vulnerabilities()
