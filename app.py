from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import func
from datetime import datetime, timedelta
# 导入你的数据库对象和模型
from models import db, SecurityEvent 

app = Flask(__name__)
CORS(app) # 允许跨域，虽然小程序开发工具可以关闭校验，但建议加上

# 数据库连接配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Abc123@localhost/llm_sec_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ---------------------------------------------------------
# 接口 1: 专门给小程序【告警列表】提供数据
# ---------------------------------------------------------
@app.route('/api/get_alerts', methods=['GET'])
def get_alerts():
    # 获取过滤参数
    risk_level = request.args.get('risk_level')
    
    query = SecurityEvent.query
    
    # 如果前端传了非“全部”的过滤条件
    if risk_level and risk_level != '全部':
        # 注意：这里的 .risk_level 必须是你 models.py 里的真实字段名
        query = query.filter(SecurityEvent.risk_level == risk_level)
    
    # 按照发布时间倒序排列，取最新的 50 条展示（避免 1948 条一次性加载太慢）
    events = query.order_by(SecurityEvent.publish_time.desc()).limit(50).all()
    
    # 将模型对象转为小程序识别的 JSON 格式
    alert_list = []
    for e in events:
        alert_list.append({
            "id": e.id,
            "event_name": getattr(e, 'title', '未知攻击'),  # 映射数据库 title
            "severity": getattr(e, 'risk_level', '中危'),    # 映射数据库 risk_level
            "model_name": getattr(e, 'target_model', 'LLM-Model'), 
            "description": getattr(e, 'content', '')[:60] + "...", # 截取摘要
            "created_at": e.publish_time.strftime('%Y-%m-%d %H:%M') if e.publish_time else "未知时间",
            "attack_type": getattr(e, 'category', '通用注入')
        })
    
    return jsonify(alert_list)

# ---------------------------------------------------------
# 接口 2: 获取单条详情（点击详情页时用）
# ---------------------------------------------------------
@app.route('/api/event_detail/<int:event_id>', methods=['GET'])
def get_event_detail(event_id):
    event = SecurityEvent.query.get_or_404(event_id)
    # 构造详情页需要的完整数据
    return jsonify({
        "id": event.id,
        "event_name": event.title,
        "severity": event.risk_level,
        "model_name": getattr(event, 'target_model', 'GPT-4'),
        "description": event.content,
        "created_at": event.publish_time.strftime('%Y-%m-%d %H:%M:%S') if event.publish_time else "",
        "attack_type": event.category
    })

# ---------------------------------------------------------
# 接口 3: 你原有的统计接口（用于仪表盘图表）
# ---------------------------------------------------------
@app.route('/api/stats/category', methods=['GET'])
def get_category_stats():
    stats = db.session.query(
        SecurityEvent.category, 
        func.count(SecurityEvent.id)
    ).group_by(SecurityEvent.category).all()
    
    return jsonify([{"name": s[0] if s[0] else "其他", "value": s[1]} for s in stats])

@app.route('/api/stats/trend', methods=['GET'])
def get_trend_stats():
    days = request.args.get('days', 7, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    stats = db.session.query(
        func.date(SecurityEvent.publish_time).label('date'),
        func.count(SecurityEvent.id)
    ).filter(SecurityEvent.publish_time >= start_date)\
     .group_by('date')\
     .order_by('date').all()
     
    return jsonify([{"date": str(s[0]), "count": s[1]} for s in stats])

@app.route('/')
def index():
    return "<h1>LLM 安全监控后端已启动</h1><p>API 状态: 正常</p>"

if __name__ == '__main__':
    # host='0.0.0.0' 允许局域网访问，方便手机预览
    app.run(debug=True, host='0.0.0.0', port=5000)