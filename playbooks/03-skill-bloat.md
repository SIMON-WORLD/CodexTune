# 03 - skill / 插件上下文超预算

## 现象

日志出现：

```
truncated skill metadata to fit skills context budget budget_limit=4000 total_skills=294 included_skills=220 omitted_skills=74
```

表示 skill 数量超出上下文预算，部分 skill 元数据被截断或丢弃。

## 处理

1. 统计 SKILL.md 数量：`.codex\skills`、`.agents\skills`、项目 `.agents\skills`、`plugins\cache`。
2. 分析实际使用：扫描会话记录中 skill 名称出现次数，区分“目录里挂着”和“真正用过”。
3. 未使用的成套 skill（如产品/GTM 包）移出项目目录，保留备份。
4. 重启后对比日志中的 total_skills / omitted_skills。

## 注意

- 移出不是删除：保留到可恢复位置。
- `.agents\skills` 是工具识别路径，不要改名或编号。
