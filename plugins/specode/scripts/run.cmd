@echo off
REM specode plugin python launcher (Windows).
REM 依次探测 python3 / python / py，找到就 call 并透传所有参数。
REM 全部失败时 exit /B 127 + 提示。

where python3 >NUL 2>&1
if %ERRORLEVEL%==0 (
  python3 %*
  exit /B %ERRORLEVEL%
)

where python >NUL 2>&1
if %ERRORLEVEL%==0 (
  python %*
  exit /B %ERRORLEVEL%
)

where py >NUL 2>&1
if %ERRORLEVEL%==0 (
  py -3 %*
  exit /B %ERRORLEVEL%
)

echo specode: 未找到可用的 Python 解释器（已尝试 python3 / python / py）。 1>&2
echo         请安装 Python 3.8+ 并确保其位于 PATH 中后再次重试。 1>&2
exit /B 127
