import json
from datetime import datetime


def _items(values, empty="暂无"):
    if not values:
        return f"- {empty}"
    lines = []
    for value in values:
        if isinstance(value, dict):
            title = value.get("requirement") or value.get("target") or "分析项"
            details = value.get("reason") or value.get("suggestion") or ""
            evidence = value.get("evidence")
            line = f"- **{title}**"
            if evidence:
                line += f"｜证据：{evidence}"
            if details:
                line += f"｜{details}"
            lines.append(line)
        else:
            lines.append(f"- {value}")
    return "\n".join(lines)


def build_markdown_report(result: dict) -> str:
    job = result.get("job_info", {})
    match = result.get("match_result", {})
    breakdown = match.get("score_breakdown", {})
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""# JobPilot 简历与岗位匹配分析报告

生成时间：{generated_at}

## 岗位概览

- 岗位：{job.get('job_title') or '未识别'}
- 公司：{job.get('company') or '未识别'}
- 岗位类型：{job.get('job_type') or '未识别'}
- 关键词：{', '.join(job.get('keywords', [])) or '暂无'}

## 匹配结论

**综合匹配分数：{match.get('match_score', 0)}/100**

{match.get('summary') or '暂无总结'}

评分拆解：核心要求 {breakdown.get('core_requirements', 0)}/40；相关经历 {breakdown.get('relevant_experience', 0)}/30；技能工具 {breakdown.get('skills_tools', 0)}/20；加分项 {breakdown.get('bonus_items', 0)}/10。

## 明确匹配

{_items(match.get('strong_matches', []))}

## 部分匹配

{_items(match.get('partial_matches', []))}

## 关键词缺口

{_items(match.get('keyword_gaps', []))}

## 能力差距

{_items(match.get('gaps', []))}

## 待确认信息

{_items(match.get('unknowns', []))}

## 简历修改建议

{_items(match.get('improvement_suggestions', []))}

## 优先行动

{_items(match.get('priority_actions', []))}

---

本报告由AI辅助生成，仅依据上传简历与岗位JD，不代表招聘结果；请人工核验后使用。
"""


def build_json_report(result: dict) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2)
