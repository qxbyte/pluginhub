---
description: 结束当前 specode 持久会话（不删除文档）
---

/specode:end

> 注：执行本命令时必须调用 `spec_session.py end --session <session_id>`，强制写入 `mode=ended` 并释放锁；in-memory 半成功不被允许。
