# Design and Development of a WeChat Mini Program for Security Incident Alerting in Large Language Models

本项目采用前后端分离架构，后端基于 Python 的 Flask 框架开发，负责 NVD 漏洞拉取、AVID 情报同步、Gemini API 驱动的 AI 红队对抗样本合成，以及 TF-IDF 与逻辑回归模型自动标注等核心逻辑，依托 Python 在 NLP 与自动化领域的优势，构建低延迟、高稳定的大模型安全态势感知系统。前端基于微信小程序原生框架，使用 JavaScript、WXML、WXSS 实现交互与界面，并集成 ECharts 动态展示全球大模型安全事件分布与趋势，打造即用即走的移动端安全分析工具，适用于企业级大模型合规审计、AIGC 风险监控与智能体权限防御等场景。

---

### 项目声明

- **项目名称**：大模型安全态势感知与自动化分类告警系统
- **项目作者**：CHU KIN YUNG
- **作者单位**：暨南大学网络空间安全学院
- **开发语言**：Python / JavaScript
- **核心框架**：Flask (后端) / 微信小程序原生框架 (前端)
- **核心技术**：TF-IDF 文本向量化、逻辑回归多分类（Logistic Regression）、生成式 AI 红队对抗合成、多源异构爬虫、多进程自动化调度、ECharts 动态数据可视化

---

### 项目目录结构

├── weixin_xiaochengxu/     # 微信小程序前端代码（包含 ECharts 态势感知驾驶舱）
├── ablation_study_dictionary.py  # 消融实验模块（验证安全专用词典在分词策略中的必要性）
├── ai_collector.py         # 主动红队生成模块（基于 Gemini API 自动合成前沿未知安全对抗样本）
├── nvd_collector.py        # 被动采集模块 1（基于 NVD NIST API 同步权威大模型漏洞数据）
├── avid_github_importer.py # 被动采集模块 2（导入 AVID GitHub 开源安全漏洞 JSON 报告）
├── avid_crawler.py         # 被动采集模块 3（针对 AVID 社区大模型风险事件的网络舆情爬虫）
├── crawler_pro.py          # 网络安全情报进阶多线程爬虫
├── final_classifier.py     # NLP 智能分类引擎（TF-IDF + 逻辑回归多分类打标流水线）
├── models.py               # 数据库 ORM 实体定义（SecurityEvent 模型，支持 MySQL 与 SQLite）
├── app.py                  # Flask 后端 API 服务入口（提供告警列表、单条详情与可视化聚合数据接口）
├── run_scheduler.py        # 核心任务调度器（实现 3 小时周期性自动轮询、进程隔离与容错）
├── data_export.csv         # 包含 1.2 万条真实标注的安全事件评估数据集（用于训练与消融）
├── evaluate_model_performance.py # 分类器模型交叉验证与混淆矩阵性能评估脚本
├── evaluate_csv_performance.py   # 用于快速统计当前导出数据量化指标的评估工具
├── security_user_dict.txt  # 安全领域专用分词词典（保障 Prompt Injection 等术语语义完整性）
├── scheduler.log           # 调度器自动化运行历史日志
├── requirements.txt        # 后端依赖 Python 库列表
└── README.md               # 本项目说明文档

###核心系统工作流程
- **多源采集（Perception）**：run_scheduler.py 周期性唤醒进程，多源抓取 NVD 与 AVID 上的 LLM 漏洞，同时通过 ai_collector.py 诱导 Gemini 自动批量合成前沿对抗语料，无感知写入数据库缓冲区。
- **智能打标（Decision）**：一旦新数据写入，final_classifier.py 自动加载 security_user_dict.txt 安全词典进行 jieba 分词，通过 TF-IDF 映射为特征矩阵，利用已部署的逻辑回归平衡分类器解算 OWASP 标准的概率分布，并原子级更新分类标签。
- **敏捷触达（Action）**：移动端微信小程序调用 app.py 的 RESTful 端点，将最新的结构化安全情报和危害评级以 ECharts 数据图表、PoC 安全预览等形式丝滑渲染呈现，并触发微信订阅预警消息。
