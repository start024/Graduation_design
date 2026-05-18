# Design and Development of a WeChat Mini Program for Security Incident Alerting in Large Language Models

本项目采用前后端分离架构，后端基于 Python 的 Flask 框架开发，负责 NVD 漏洞拉取、AVID 情报同步、Gemini API 驱动的 AI 红队对抗样本合成，以及 TF-IDF 与逻辑回归模型自动标注等核心逻辑，依托 Python 在 NLP 与自动化领域的优势，构建低延迟、高稳定的大模型安全态势感知系统。前端基于微信小程序原生框架，使用 JavaScript、WXML、WXSS 实现交互与界面，并集成 ECharts 动态展示全球大模型安全事件分布与趋势，打造即用即走的移动端安全分析工具，适用于企业级大模型合规审计、AIGC 风险监控与智能体权限防御等场景。

---

### 项目声明

- **项目名称**：JPEG 图像加解密服务系统
- **项目作者**：Chen Yanfeng
- **作者单位**：暨南大学网络空间安全学院
- **开发语言**：Python
- **核心框架**：Flask
- **核心技术**：JPEG 编解码、DCT 域加解密、图像隐私保护

---

### 项目目录结构

```text
├── data/
│   ├── upload_images/      # 存放上传的原始图像
│   ├── cipher_images/      # 存放加密后的密文图像
│   └── decrypt_images/     # 存放解密后的还原图像
├── Encryption/             # 加密算法模块
│   ├── __init__.py
│   ├── AC_encryption.py    # AC系数加密
│   ├── DC_encryption.py    # DC系数加密
│   ├── encryption.py       # 主加密逻辑
│   ├── invzigag.py         # 逆Zigzag扫描
│   ├── utils.py            # 工具函数
│   └── zigzag.py           # Zigzag扫描
├── Decryption/             # 解密算法模块
│   └── ...                 # (此处补充解密相关文件)
├── app.py                  # Flask 启动入口
├── requirements.txt        # 依赖库列表
└── README.md               # 项目说明文档
