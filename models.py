from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class SecurityEvent(db.Model):
    __tablename__ = 'security_events'
    
    id = db.Column(db.Integer, primary_key=True)
    # 事件标题
    title = db.Column(db.String(255), nullable=False)
    # 来源平台，例如 HuggingFace
    source = db.Column(db.String(100))
    # 基于 OWASP 框架的分类标签
    category = db.Column(db.String(100))
    # 原始文本内容，用于后续 NLP 语义分析
    content = db.Column(db.Text)
    # 事件发布或抓取时间 
    publish_time = db.Column(db.DateTime, default=datetime.datetime.now)
    # 风险等级（高/中/低）
    risk_level = db.Column(db.String(50))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "category": self.category,
            "content": self.content,
            "risk_level": self.risk_level,
            "publish_time": self.publish_time.strftime('%Y-%m-%d %H:%M:%S') if self.publish_time else None
        }