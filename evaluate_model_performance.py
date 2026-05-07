import pandas as pd
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from app import app
from models import db, SecurityEvent

def evaluate_performance():
    print("🚀 正在从数据库加载真实数据进行性能评估...")
    
    with app.app_context():
        # 1. 获取所有已标准分类的数据（排除 Others 和空标签）
        all_events = SecurityEvent.query.filter(
            SecurityEvent.category.isnot(None),
            SecurityEvent.category != 'Others',
            SecurityEvent.category != ''
        ).all()
        
        if len(all_events) < 50:
            print(f"\n⚠️ 警告：当前已标定数据量仅为 {len(all_events)} 条，样本不足可能导致指标波动较大。建议数据量 > 100 条再进行正式评估。")
        else:
            print(f"✅ 找到 {len(all_events)} 条有效标注样本。")

        if not all_events:
            print("❌ 错误：数据库中没有已标注的样本，请先运行数据采集和初步打标。")
            return

        # 2. 准备数据
        data = []
        for e in all_events:
            # 模拟 final_classifier.py 的分词逻辑
            text = " ".join(jieba.cut(f"{e.title} {e.content}"))
            data.append({"text": text, "label": e.category})
        
        df = pd.DataFrame(data)
        
        # 检查类别分布
        counts = df['label'].value_counts()
        print("\n📊 各类别样本分布 (已标注)：")
        print(counts)
        
        # 过滤掉样本数过少的类别（至少需要 2 个样本才能拆分训练/测试）
        valid_labels = counts[counts >= 2].index
        if len(valid_labels) < 2:
            print("❌ 错误：满足条件的类别数太少，无法进行对比评估。")
            return
            
        df = df[df['label'].isin(valid_labels)]

        # 3. 拆分训练集和测试集 (80/20)
        X_train, X_test, y_train, y_test = train_test_split(
            df['text'], df['label'], test_size=0.2, random_state=42, stratify=df['label']
        )

        # 4. 训练 TF-IDF + 逻辑回归
        vectorizer = TfidfVectorizer(max_features=1000)
        X_train_vec = vectorizer.fit_transform(X_train)
        X_test_vec = vectorizer.transform(X_test)

        # 采用与生产环境一致的平衡权重配置
        model = LogisticRegression(class_weight='balanced', max_iter=1000)
        model.fit(X_train_vec, y_train)

        # 5. 生成真实评估报告
        y_pred = model.predict(X_test_vec)
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # 打印精简版结果
        print("\n" + "="*70)
        print("🏆 真实分类模型性能报告 (Real Evaluation Report)")
        print("="*70)
        print(f"{'OWASP 类别 (OWASP Category)':<40} | {'精确率':<8} | {'F1 分数':<8}")
        print("-" * 70)
        
        for label, metrics in report.items():
            if label in ['accuracy', 'macro avg', 'weighted avg']:
                continue
            print(f"{label:<40} | {metrics['precision']:.2f}     | {metrics['f1-score']:.2f}")
        
        print("-" * 70)
        print(f"总准确率 (Overall Accuracy): {report['accuracy']:.2%}")
        print("="*70)
        print("\n💡 提示：您可以直接将上述表格中的数据填入论文中。")

if __name__ == "__main__":
    evaluate_performance()
