import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import jieba
from app import app
from models import db, SecurityEvent

# 定义标准的 OWASP 映射关系
OWASP_MAPPING = {
    'Prompt Injection': 'LLM01: Prompt Injection',
    'Model Jailbreak': 'LLM01: Prompt Injection',
    'Data Exposure': 'LLM06: Sensitive Data Disclosure',
    'Sensitive Data Disclosure': 'LLM06: Sensitive Data Disclosure',
    'Training Data Poisoning': 'LLM03: Training Data Poisoning',
    'Supply Chain': 'LLM05: Supply Chain Vulnerabilities',
    'Insecure Output Handling': 'LLM02: Insecure Output Handling',
    'Model Theft': 'LLM10: Model Theft'
}

def standardize_and_classify():
    with app.app_context():
        # 1. 关键词预处理：将现有零散标签标准化
        events = SecurityEvent.query.all()
        for e in events:
            if e.category in OWASP_MAPPING:
                e.category = OWASP_MAPPING[e.category]
        db.session.commit()

        # 2. 准备 NLP 训练数据
        data = []
        all_events = SecurityEvent.query.all()
        for e in all_events:
            text = " ".join(jieba.cut(f"{e.title} {e.content}"))
            data.append({"id": e.id, "text": text, "label": e.category})
        
        df = pd.DataFrame(data)
        train_df = df[df['label'].str.contains('LLM')] # 只用已确定的标准标签训练

        if len(train_df) < 5:
            print("标准样本不足，请先手动运行一次关键词分类器或手动标注几个 LLMxx 标签。")
            return

        # 3. 训练 TF-IDF + 逻辑回归模型
        vectorizer = TfidfVectorizer(max_features=1000)
        X_train = vectorizer.fit_transform(train_df['text'])
        y_train = train_df['label']

        model = LogisticRegression(class_weight='balanced')
        model.fit(X_train, y_train)

        # 4. 对剩余的 Others 或 NLP 临时标签进行最终打标
        target_events = SecurityEvent.query.filter(
            (SecurityEvent.category == 'Others') | (SecurityEvent.category.like('NLP:%'))
        ).all()

        for event in target_events:
            text_cut = " ".join(jieba.cut(f"{event.title} {event.content}"))
            X_pred = vectorizer.transform([text_cut])
            prediction = model.predict(X_pred)[0]
            event.category = prediction # 直接应用标准 OWASP 标签

        db.session.commit()
        print(f"SUCCESS: 成功完成基于 OWASP 框架的自动打标，处理了 {len(target_events)} 条事件。")

if __name__ == "__main__":
    standardize_and_classify()