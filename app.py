from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import func
from datetime import datetime, timedelta
from models import db, SecurityEvent

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Abc123@localhost/llm_sec_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return "<h1>后端运行正常！</h1><p>请访问 <a href='/api/events'>/api/events</a> 查看 JSON 数据。</p>"

@app.route('/api/events', methods=['GET'])
def get_events():
    # Pagination
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    # Filtering
    risk_level = request.args.get('risk_level')
    category = request.args.get('category')
    
    query = SecurityEvent.query
    
    if risk_level:
        query = query.filter(SecurityEvent.risk_level == risk_level)
    if category:
        query = query.filter(SecurityEvent.category == category)
        
    # Order by latest
    query = query.order_by(SecurityEvent.publish_time.desc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    events = pagination.items
    
    return jsonify({
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
        "data": [event.to_dict() for event in events]
    })

@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_event_detail(event_id):
    event = SecurityEvent.query.get_or_404(event_id)
    return jsonify(event.to_dict())

@app.route('/api/stats/category', methods=['GET'])
def get_category_stats():
    # Aggregation for pie chart
    stats = db.session.query(
        SecurityEvent.category, 
        func.count(SecurityEvent.id)
    ).group_by(SecurityEvent.category).all()
    
    result = [{"name": s[0] if s[0] else "Unknown", "value": s[1]} for s in stats]
    return jsonify(result)

@app.route('/api/stats/trend', methods=['GET'])
def get_trend_stats():
    # Last 7 days trend for line chart
    days = request.args.get('days', 7, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    # A simple approach for MySQL date formatting
    stats = db.session.query(
        func.date(SecurityEvent.publish_time).label('date'),
        func.count(SecurityEvent.id)
    ).filter(SecurityEvent.publish_time >= start_date)\
     .group_by('date')\
     .order_by('date').all()
     
    # Convert dates to string format
    result = [{"date": str(s[0]), "count": s[1]} for s in stats]
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)