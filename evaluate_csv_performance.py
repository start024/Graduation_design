import pandas as pd
import jieba
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

def evaluate_csv_performance():
    csv_path = 'data_export.csv'
    if not os.path.exists(csv_path):
        print(f"Error: File {csv_path} not found")
        return

    print(f"Starting performance evaluation from {csv_path}...")
    
    # Read CSV with encoding fallback
    try:
        df = pd.read_csv(csv_path, sep='\t', encoding='utf-8')
    except:
        try:
            df = pd.read_csv(csv_path, sep='\t', encoding='utf-16')
        except:
            df = pd.read_csv(csv_path, sep='\t', encoding='gbk')

    # Filter invalid data
    df = df.dropna(subset=['title', 'category'])
    df = df[df['category'] != 'Others']
    
    print(f"Successfully loaded {len(df)} valid samples.")

    # 1. Processing (using jieba)
    print("Tokenizing text...")
    df['text'] = df['title'].apply(lambda x: " ".join(jieba.cut(str(x))))

    # 2. Category distribution
    counts = df['category'].value_counts()
    print("\nSample distribution (Top 10):")
    print(counts.head(10))

    # Filter out small classes
    valid_labels = counts[counts >= 5].index
    df_filtered = df[df['category'].isin(valid_labels)]

    # 3. Train/Test split
    X_train, X_test, y_train, y_test = train_test_split(
        df_filtered['text'], df_filtered['category'], test_size=0.2, random_state=42, stratify=df_filtered['category']
    )

    # 4. Vectorization and Classification
    vectorizer = TfidfVectorizer(max_features=1000)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(class_weight='balanced', max_iter=1000)
    model.fit(X_train_vec, y_train)

    # 5. Generate report
    y_pred = model.predict(X_test_vec)
    report = classification_report(y_test, y_pred, output_dict=True)

    print("\n" + "="*70)
    print("Real Classification Performance Report (based on data_export.csv)")
    print("="*70)
    print(f"{'OWASP Category':<40} | {'Precision':<8} | {'F1-Score':<8}")
    print("-" * 70)
    
    for label, metrics in report.items():
        if label in ['accuracy', 'macro avg', 'weighted avg']:
            continue
        print(f"{label:<40} | {metrics['precision']:.2f}     | {metrics['f1-score']:.2f}")
    
    print("-" * 70)
    print(f"Overall Accuracy: {report['accuracy']:.2%}")
    print("="*70)
    print("\nTip: You can copy the data above into your thesis.")

if __name__ == "__main__":
    # Ensure pandas, jieba, and sklearn are in the environment
    try:
        evaluate_csv_performance()
    except Exception as e:
        print(f"Execution failed: {e}")
