import subprocess
import time
import datetime
import sys
import os

# 配置要运行的任务列表及其对应的脚本文件名
TASKS = [
    "nvd_collector.py",
    "avid_github_importer.py",
    "avid_crawler.py",
    "ai_collector.py",
    "final_classifier.py"
]

LOG_FILE = "scheduler.log"
INTERVAL_SECONDS = 3 * 3600  # 3 小时

def log_message(msg):
    # 移除或替换消息中的 Emoji 以防控制台显示乱码
    clean_msg = msg.replace("🚀", "[Start]").replace("🛑", "[Stop]").replace("📊", "[Stats]").replace("😴", "[Sleep]").replace("❌", "[Error]")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {clean_msg}"
    print(full_msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(full_msg + "\n")
    except:
        pass

def run_task(script_name):
    log_message(f"开始运行任务: {script_name}")
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_dir, script_name)
        
        # 核心修复点：强制设置子进程环境变量为 UTF-8，确保 Emoji 不会引发崩溃
        my_env = os.environ.copy()
        my_env["PYTHONIOENCODING"] = "utf-8"
        
        # 核心修复点 2：使用 sys.executable (绝对路径) 而不是 "python" 关键字
        # 这样即使 CMD PATH 没配好也能找到当前运行的 Python
        python_exe = sys.executable
        
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n--- {script_name} 输出开始 ---\n")
            # 在 Windows 上，这种列表形式最安全，不需要 shell=True
            result = subprocess.run(
                [python_exe, script_path], 
                cwd=base_dir,
                env=my_env,
                stdout=f,
                stderr=f,
                text=True
            )
            f.write(f"--- {script_name} 输出结束 ---\n")
            
        log_message(f"任务完成: {script_name} (状态码: {result.returncode})")
        return result.returncode == 0
    except Exception as e:
        log_message(f"任务 {script_name} 运行系统失败: {e}")
        return False

def main():
    log_message("自动化调度器已启动，设定间隔：3 小时")
    
    while True:
        log_message("=== 开始一轮完整的数据同步与分类任务 ===")
        start_time = time.time()
        
        success_count = 0
        for task in TASKS:
            if run_task(task):
                success_count += 1
            time.sleep(5) 
            
        log_message(f"本轮结束。成功: {success_count}/{len(TASKS)}")
        
        wait_time = max(0, INTERVAL_SECONDS - (time.time() - start_time))
        log_message(f"调度器进入休眠，大约将在 {wait_time/3600:.2f} 小时后重启...")
        time.sleep(wait_time)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("调度器由用户停止 (Ctrl+C)")
    except Exception as e:
        with open("critical_error.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now()}] 核心调度器崩溃: {e}\n")
        print(f"核心调度器崩溃: {e}")
