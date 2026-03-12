import requests
from bs4 import BeautifulSoup
from models import db, SecurityEvent
from app import app

def crawl_avid_blog():
    url = "https://avidml.org/blog/" # 任务书指定的来源 [cite: 19, 87]
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # AVID Blog 的结构通常在 article 或 h2 标签中
        posts = soup.find_all('h2') 
        
        with app.app_context():
            for post in posts:
                title = post.text.strip()
                link = post.find('a')['href'] if post.find('a') else ""
                
                if title and not SecurityEvent.query.filter_by(title=title).first():
                    new_event = SecurityEvent(
                        title=title,
                        source="AVID-ML",
                        content=f"详情链接: {link}",
                        category="Others", # 爬虫初步分类设为 Others，后续靠 NLP 修正 
                        risk_level="中"
                    )
                    db.session.add(new_event)
            db.session.commit()
            print("AVID-ML 数据抓取完成！")
    except Exception as e:
        print(f"爬虫出错: {e}")

if __name__ == "__main__":
    crawl_avid_blog()