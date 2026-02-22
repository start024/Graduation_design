import os
import requests
from bs4 import BeautifulSoup
from models import db, SecurityEvent
from app import app
import datetime

# 代理配置
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7897"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"

def crawl_avid_database():
    # 目标转向 AVID 的数据库预览页
    url = "https://avidml.org/database/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print(f"[{datetime.datetime.now()}] 正在抓取 AVID-ML 漏洞数据库摘要...")
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # AVID 数据库页面的条目通常在表格或特定列表容器中
        # 根据当前页面结构，我们提取所有包含 AVID 编号的链接或文本
        entries = soup.find_all('tr') # 尝试抓取表格行
        
        with app.app_context():
            count = 0
            for row in entries:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    avid_id = cols[0].get_text().strip() # 如 AVID-2023-V001
                    title = cols[1].get_text().strip()
                    description = cols[2].get_text().strip()
                    
                    full_title = f"[{avid_id}] {title}"
                    
                    if not SecurityEvent.query.filter_by(title=full_title).first():
                        event = SecurityEvent(
                            title=full_title,
                            source="AVID-ML",
                            category="Others", # 待后续 NLP 自动打标
                            content=description,
                            risk_level="高",
                            publish_time=datetime.datetime.now()
                        )
                        db.session.add(event)
                        count += 1
            
            db.session.commit()
            print(f"AVID-ML 数据库采集完成，新增 {count} 条。")
            
    except Exception as e:
        print(f"爬虫运行出错: {e}")

if __name__ == "__main__":
    crawl_avid_database()