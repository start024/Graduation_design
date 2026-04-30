import os
import requests
import json
import time
import datetime
from app import app
from models import db, SecurityEvent
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 1. 代理配置（确保端口与 Clash 一致）
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7897"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"

def get_session():
    """创建一个带有重试机制的 session"""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def import_avid_github_data():
    base_url = "https://raw.githubusercontent.com/avidml/avid-db/main/data/"
    print(f"[{datetime.datetime.now()}] 正在启动增强版同步程序...")

    session = get_session()
    headers = {"User-Agent": "Mozilla/5.0"}

    with app.app_context():
        count = 0
        # 扩展抓取范围：同时抓取 漏洞(V) 和 报告(R)
        years = ['2023', '2024']
        types = [('vulnerability', 'V'), ('report', 'R')]
        
        for year in years:
            for type_name, prefix in types:
                print(f"正在同步 {year} 年的 {type_name} 类型数据...")
                for i in range(1, 401): # 尝试抓取每种类型的前 400 个
                    vuln_id = f"AVID-{year}-{prefix}{str(i).zfill(3)}" 
                    file_url = f"{base_url}{type_name}/{vuln_id}.json"
                    
                    try:
                        res = session.get(file_url, headers=headers, timeout=10)
                        
                        if res.status_code == 200:
                            data = res.json()
                            # 统一来源标签为 AVID-ML 方便统计
                            title = f"{vuln_id}: {data.get('vuln_id', data.get('report_id', ''))}"
                            full_content = data.get('description', {}).get('value', 'No description available')
                            
                            if not SecurityEvent.query.filter_by(title=title).first():
                                event = SecurityEvent(
                                    title=title[:255],
                                    source="AVID-ML",
                                    content=full_content,
                                    category="Others",
                                    risk_level="中",
                                    publish_time=datetime.datetime.now()
                                )
                                db.session.add(event)
                                count += 1
                                print(f"SUCCESS: 成功获取: {vuln_id}")
                        else:
                            print(f"跳过 {vuln_id} (状态码: {res.status_code})")
                        
                        # 每抓取一个休息 1 秒，防止被 GitHub 封 IP
                        time.sleep(1)
                        
                        if count % 5 == 0 and count > 0:
                            db.session.commit()

                    except Exception as e:
                        print(f"ERROR: 处理 {vuln_id} 发生网络故障: {e}，休息 5 秒...")
                        time.sleep(5)
                        continue

        db.session.commit()
        print(f"\nDONE: 同步结束！本次新增 {count} 条权威数据。")

if __name__ == "__main__":
    import_avid_github_data()
