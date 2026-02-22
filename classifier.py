from app import app
from models import db, SecurityEvent

# 定义 OWASP LLM 核心关键词矩阵
OWASP_CATEGORIES = {
    "LLM01: Prompt Injection": ["jailbreak", "prompt injection", "override", "提示注入", "越狱", "绕过"],
    "LLM02: Insecure Output Handling": ["xss", "cross-site scripting", "output validation", "输出处理"],
    "LLM03: Training Data Poisoning": ["poisoning", "backdoor", "fine-tuning", "数据投毒", "训练数据"],
    "LLM05: Supply Chain Vulnerabilities": ["hugging face", "pytorch", "dependency", "供应链", "第三方库"],
    "LLM06: Sensitive Data Disclosure": ["pii", "leakage", "privacy", "disclosure", "隐私泄露", "敏感数据"],
    "LLM07: Insecure Plugin Design": ["plugin", "tool use", "agent access", "插件安全"],
    "LLM09: Improper Inventory Management": ["versioning", "stale model", "inventory", "版本管理"],
    "LLM10: Model Theft": ["extraction", "stealing", "copying", "模型窃取", "逆向工程"]
}

def classify_events():
    with app.app_context():
        # 获取所有分类为 'Others' 或 需要重新分类的事件
        events = SecurityEvent.query.all()
        updated_count = 0
        
        for event in events:
            text = (event.title + " " + event.content).lower()
            old_category = event.category
            
            # 语义关键词匹配
            for category, keywords in OWASP_CATEGORIES.items():
                if any(kw in text for kw in keywords):
                    event.category = category
                    break # 匹配到一个就跳出
            
            if old_category != event.category:
                updated_count += 1
        
        db.session.commit()
        print(f"分类完成！共更新了 {updated_count} 条事件的分类标签。")

if __name__ == "__main__":
    classify_events()