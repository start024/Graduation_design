import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from app import app
from models import db, SecurityEvent

def train_and_classify():
    with app.app_context():
        # 1. 获取已分类的数据作为训练集
        events = SecurityEvent.query.all()
        data = [{"text": e.title + " " + e.content, "label": e.category} for e in events]
        df = pd.DataFrame(data)

        # 过滤掉 Others 标签，只训练已明确分类的
        train_df = df[df['label'] != 'Others']
        
        if len(train_df) < 20: # 训练样本太少时先跳过
            print("已标注数据不足，请先增加数据或手动标注一部分。")
            return

        # 2. 特征工程：TF-IDF (将文本转为数字矩阵)
        vectorizer = TfidfVectorizer(max_features=1000)
        X = vectorizer.fit_transform(train_df['text'])
        y = train_df['label']

        # 3. 训练逻辑回归模型 (Logistic Regression)
        model = LogisticRegression()
        model.fit(X, y)

        # 4. 对所有 'Others' 标签的数据进行预测
        others_events = SecurityEvent.query.filter_by(category='Others').all()
        for event in others_events:
            text_vec = vectorizer.transform([event.title + " " + event.content])
            prediction = model.predict(text_vec)[0]
            
            # 更新分类 (直接赋予真实的类别，不加前缀，避免图表分裂)
            event.category = prediction 
        
        db.session.commit()
        print(f"机器学习分类完成，更新了 {len(others_events)} 条数据。")

if __name__ == "__main__":
    train_and_classify()