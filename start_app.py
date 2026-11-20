import subprocess
import sys
import os

os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
os.environ['STREAMLIT_SERVER_PORT'] = '8501'
os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'

# 用 stdin 連接到 /dev/null 以避免交互提示
process = subprocess.Popen(
    [sys.executable, '-m', 'streamlit', 'run', 'app_streamlit.py'],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT
)

# 打印輸出
for line in iter(process.stdout.readline, b''):
    print(line.decode('utf-8', errors='replace').strip())

process.wait()
