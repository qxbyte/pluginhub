"""ragkit_hooks.py 的 SessionStart bootstrap 编码回归测试。

背景：Windows Python 重定向管道的 `sys.stdout.write()` 默认用 locale 编码
（中文环境 cp936/GBK），会把中文 bootstrap 写成 GBK 字节；宿主按 UTF-8 读取
即乱码（实测本会话 SessionStart 注入显示成 `RagKit ���ã�...`）。修法是 hook
显式写 UTF-8 字节（`sys.stdout.buffer.write(...encode("utf-8"))`）。

用 `PYTHONIOENCODING=gbk` 模拟中文 Windows 的重定向管道，可在任意 OS 上确定性
复现——未修前 hook 会吐 GBK 字节（下面的 UTF-8 解码会抛错），修好后恒为 UTF-8。
"""
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def test_session_start_hook_emits_utf8_under_non_utf8_locale():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "gbk"  # 模拟中文 Windows 重定向管道
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "ragkit_hooks.py")],
        input=b"", capture_output=True, env=env,  # bytes 模式，拿原始字节
    )
    assert proc.returncode == 0
    # 必须是合法 UTF-8，且中文 bootstrap 完整（GBK 字节会在此抛 UnicodeDecodeError）
    text = proc.stdout.decode("utf-8")
    assert "RagKit" in text
    assert "knowledge-base" in text
    assert "SessionStart" in text
