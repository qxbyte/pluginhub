#!/bin/sh
# specode plugin python launcher (POSIX).
# 依次探测 python3 / python / py，找到就 exec 并透传所有参数。
# 全部失败时 exit 127 + stderr 提示。

set -u

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python "$@"
fi

if command -v py >/dev/null 2>&1; then
  exec py -3 "$@"
fi

printf '%s\n' "specode: 未找到可用的 Python 解释器（已尝试 python3 / python / py）。" >&2
printf '%s\n' "        请安装 Python 3.8+ 并确保其位于 PATH 中后再次重试。" >&2
exit 127
