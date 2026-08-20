import os
import hashlib
from datetime import datetime, timezone
from io import BytesIO

import streamlit as st
from streamlit_paste_button import paste_image_button

from agents.career_agent import CareerAgent
from utils.file_parser import extract_text_bytes
from utils.llm import create_client
from utils.ocr import extract_text_from_image
from utils.report import build_json_report, build_markdown_report
from utils.resume_export import build_docx_bytes, build_pdf_bytes

st.set_page_config(page_title="JobPilot｜AI简历工作台", page_icon="✦", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&display=swap');
:root{--ink:#172033;--muted:#667085;--brand:#5b5bd6;--brand2:#8b5cf6;--line:#e6e8f0}
.stApp{background:linear-gradient(180deg,#f7f7ff 0,#fff 270px);color:var(--ink)}
html,body,[class*="css"]{font-family:Inter,"Noto Sans SC",sans-serif}.block-container{max-width:1180px;padding-top:2.1rem;padding-bottom:4rem}
.hero{padding:34px 38px;border:1px solid #e4e1ff;border-radius:24px;background:linear-gradient(135deg,#fff 0%,#f1efff 100%);box-shadow:0 18px 50px rgba(73,64,160,.09);margin-bottom:22px}
.eyebrow{color:#6558d3;font-size:13px;font-weight:700;letter-spacing:.12em;text-transform:uppercase}.hero h1{font-size:42px;line-height:1.08;margin:10px 0 12px;letter-spacing:-.04em}.hero p{color:var(--muted);font-size:16px;max-width:720px;margin:0}
.trust-row{display:flex;gap:18px;flex-wrap:wrap;margin-top:22px;color:#475467;font-size:13px}.trust-row span{background:#fff;border:1px solid var(--line);padding:7px 11px;border-radius:999px}
[data-testid="stTabs"] [data-baseweb="tab-list"]{gap:10px;background:#fff;padding:7px;border:1px solid var(--line);border-radius:14px}[data-testid="stTabs"] button[role="tab"]{border-radius:10px;padding:10px 18px;font-weight:600}[data-testid="stTabs"] button[aria-selected="true"]{background:#eeecff;color:#4f46c8}
[data-testid="stFileUploader"]{background:#fff;border:1px dashed #b8b5e8;border-radius:16px;padding:8px}[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:16px;padding:16px 18px;box-shadow:0 5px 18px rgba(16,24,40,.04)}
.resume-card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:22px 26px;box-shadow:0 8px 24px rgba(16,24,40,.05)}.step-title{font-size:20px;font-weight:700;margin:20px 0 4px}.step-sub{color:var(--muted);margin-bottom:16px}
.flow-steps{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:12px 0 24px}.flow-step{padding:10px 12px;border:1px solid var(--line);border-radius:10px;background:#fff;color:#667085;font-size:13px}.flow-step.active{background:#eeecff;border-color:#c7c2ff;color:#4f46c8;font-weight:700}.flow-step.done{background:#f0fdf4;border-color:#bbf7d0;color:#15803d}
.stButton>button[kind="primary"]{background:linear-gradient(90deg,var(--brand),var(--brand2));border:0;box-shadow:0 8px 18px rgba(91,91,214,.22)}.stButton>button,.stDownloadButton>button{border-radius:11px;min-height:44px;font-weight:600}div[data-testid="stExpander"]{border:1px solid var(--line);border-radius:12px;background:#fff}#MainMenu,footer{visibility:hidden}
</style>
""", unsafe_allow_html=True)


def get_api_key():
    try:
        return st.secrets.get("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    except Exception:
        return os.getenv("DEEPSEEK_API_KEY")


def get_agent():
    api_key = get_api_key()
    if not api_key:
        raise ValueError("未配置DEEPSEEK_API_KEY，请在环境变量或Streamlit Secrets中设置。")
    return CareerAgent(create_client(api_key))


def track_event(name, **properties):
    """Session-scoped, PII-free event record for product validation."""
    event = {
        "event": name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "properties": properties,
    }
    st.session_state.setdefault("product_events", []).append(event)


def friendly_error(exc):
    message = str(exc)
    lowered = message.lower()
    if "timeout" in lowered or "timed out" in lowered:
        return "请求超时。你的输入仍保留，可以直接重试。"
    if "connection" in lowered or "network" in lowered:
        return "网络连接失败。请检查网络后重试，当前输入不会丢失。"
    if "api_key" in lowered or "authentication" in lowered or "401" in lowered:
        return "服务暂不可用：管理员尚未正确配置模型访问权限。"
    if "rate" in lowered or "429" in lowered:
        return "当前请求较多，请稍后重试。"
    return message


def render_flow_steps(current):
    labels = ["上传材料", "AI分析", "确认与调整", "下载使用"]
    items = []
    for index, label in enumerate(labels, start=1):
        state = "done" if index < current else "active" if index == current else ""
        items.append(f'<div class="flow-step {state}">{index}. {label}</div>')
    st.markdown('<div class="flow-steps">' + "".join(items) + '</div>', unsafe_allow_html=True)


def render_items(title, items, icon):
    st.markdown(f"#### {icon} {title}")
    if not items:
        st.caption("暂无")
    for item in items or []:
        if isinstance(item, dict):
            st.markdown(f"**{item.get('requirement') or item.get('target') or '分析项'}**")
            if item.get("evidence"):
                st.caption(f"证据：{item['evidence']}")
            if item.get("reason") or item.get("suggestion"):
                st.write(item.get("reason") or item.get("suggestion"))
        else:
            st.markdown(f"- {item}")


def render_resume_preview(resume):
    with st.container(border=True):
        st.markdown(f"## {resume.get('name', '')}")
        st.caption(resume.get("contact", ""))
        if resume.get("target_role"):
            st.markdown(f"**{resume.get('target_role')}**")
        if resume.get("summary"):
            st.write(resume["summary"])
        for section in resume.get("sections", []):
            st.markdown(f"### {section.get('title', '')}")
            for entry in section.get("entries", []):
                st.markdown(f"**{entry.get('heading', '')}**　{entry.get('date', '')}")
                for bullet in entry.get("bullets", []):
                    st.markdown(f"- {bullet}")


def attach_exports(result, language, one_page=False):
    result["docx_bytes"] = build_docx_bytes(result["resume"], language=language, one_page=one_page)
    result["pdf_bytes"] = build_pdf_bytes(result["resume"], language=language, one_page=one_page)
    result["one_page"] = one_page
    return result


def render_downloads(result, suffix):
    name = result["resume"].get("name") or "Resume"
    col1, col2 = st.columns(2)
    col1.download_button("下载 Word", result["docx_bytes"], f"{name}_{suffix}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True, on_click=track_event, args=("resume_downloaded",), kwargs={"format": "docx"})
    col2.download_button("下载 PDF", result["pdf_bytes"], f"{name}_{suffix}.pdf", "application/pdf", use_container_width=True, on_click=track_event, args=("resume_downloaded",), kwargs={"format": "pdf"})


def render_feedback(context):
    key = f"feedback_{context}"
    if st.session_state.get(key):
        st.caption("感谢反馈，这会帮助我们评估结果质量。")
        return
    st.caption("这次结果对你有帮助吗？")
    good, bad, spacer = st.columns([1, 1, 5])
    if good.button("👍 有帮助", key=f"{key}_up", use_container_width=True):
        st.session_state[key] = "helpful"
        track_event("result_feedback_submitted", context=context, rating="helpful")
        st.rerun()
    if bad.button("👎 需改进", key=f"{key}_down", use_container_width=True):
        st.session_state[key] = "needs_improvement"
        track_event("result_feedback_submitted", context=context, rating="needs_improvement")
        st.rerun()


def render_resume_adjuster(state_key, source_key, language):
    result = st.session_state.get(state_key)
    if not result:
        return
    render_resume_preview(result["resume"])
    missing = result.get("missing_information", [])
    if missing:
        st.warning("没有写入正文的待补充信息：\n\n" + "\n".join(f"- {x}" for x in missing))
    if result.get("one_page"):
        st.success("当前为一页优化版：已压缩重复表述并优化页边距、行距与段落间距。")
    else:
        if st.button("一键调整为一页", key=f"{state_key}_fit_one_page", use_container_width=True):
            try:
                track_event("one_page_fit_started", language=language)
                with st.spinner("正在压缩重复内容并优化一页排版……"):
                    fitted = get_agent().fit_resume_one_page(
                        result["resume"], st.session_state[source_key], language,
                    )
                    for metadata_key in ("translation_notes", "removed_personal_information"):
                        if metadata_key in result:
                            fitted[metadata_key] = result[metadata_key]
                    st.session_state[state_key] = attach_exports(fitted, language, one_page=True)
                    st.session_state.setdefault(f"{state_key}_history", []).append({
                        "role": "assistant",
                        "content": "已调整为一页版，并同步更新 Word/PDF 下载文件。",
                    })
                track_event("one_page_fit_completed", language=language)
                st.rerun()
            except Exception as exc:
                track_event("one_page_fit_failed", language=language, error_type=type(exc).__name__)
                st.error(f"一页化失败：{friendly_error(exc)}")
    suffix = "English_Resume" if language == "en" else "JD定制简历"
    if result.get("one_page"):
        suffix += "_One_Page" if language == "en" else "_一页版"
    render_downloads(result, suffix)
    render_feedback(state_key)
    st.markdown('<div class="step-title">继续调整这份简历</div><div class="step-sub">可以连续提出要求，每次调整都会更新预览和下载文件。</div>', unsafe_allow_html=True)
    history_key = f"{state_key}_history"
    for message in st.session_state.setdefault(history_key, []):
        with st.chat_message(message["role"]):
            st.write(message["content"])
    with st.form(f"{state_key}_adjust_form", clear_on_submit=True):
        request = st.text_area("调整要求", height=90, placeholder="例如：把项目经历提前；压缩个人概述；让措辞更适合外企校招。", label_visibility="collapsed")
        submitted = st.form_submit_button("应用调整", type="primary", use_container_width=True)
    if submitted and request.strip():
        try:
            track_event("resume_adjustment_started", language=language)
            with st.spinner("正在调整并重新生成文件……"):
                adjusted = get_agent().adjust_resume(result["resume"], request, st.session_state[source_key], language)
                st.session_state[state_key] = attach_exports(
                    adjusted, language, one_page=result.get("one_page", False),
                )
            st.session_state[history_key].extend([
                    {"role": "user", "content": request},
                    {"role": "assistant", "content": "已按要求调整简历，并同步更新 Word/PDF 下载文件。"},
                ])
            track_event("resume_adjustment_completed", language=language)
            st.rerun()
        except Exception as exc:
            track_event("resume_adjustment_failed", language=language, error_type=type(exc).__name__)
            st.error(f"调整失败：{friendly_error(exc)}")


def render_jd_image_input():
    upload = st.file_uploader(
        "上传JD截图", type=["png", "jpg", "jpeg"], key="match_jd_image",
        help="支持拖拽PNG、JPG或JPEG图片。",
    )
    pasted = paste_image_button(label="或从剪贴板粘贴JD图片", key="match_jd_paste", errors="raise")
    image_bytes = None
    if pasted.image_data is not None:
        buffer = BytesIO(); pasted.image_data.save(buffer, format="PNG"); image_bytes = buffer.getvalue()
    elif upload is not None:
        image_bytes = upload.getvalue()
    if image_bytes:
        with st.expander("预览已上传的JD图片"):
            st.image(image_bytes, use_container_width=True)
        image_fingerprint = hashlib.sha256(image_bytes).hexdigest()
        previous_fingerprint = st.session_state.get("match_jd_ocr_fingerprint")
        if image_fingerprint != previous_fingerprint:
            try:
                track_event("jd_ocr_started")
                with st.spinner("JD 正在提取文字，请稍候……"):
                    text = extract_text_from_image(image_bytes)
                st.session_state.match_jd_ocr_text = text.strip()
                st.session_state.match_jd_ocr_fingerprint = image_fingerprint
                st.session_state.pop("match_jd_ocr_error", None)
                track_event("jd_ocr_completed", extracted_chars=len(text.strip()))
                st.rerun()
            except Exception as exc:
                st.session_state.match_jd_ocr_fingerprint = image_fingerprint
                st.session_state.match_jd_ocr_error = str(exc)
                track_event("jd_ocr_failed", error_type=type(exc).__name__)
        if st.session_state.get("match_jd_ocr_error"):
            st.error(f"JD文字提取失败：{friendly_error(Exception(st.session_state.match_jd_ocr_error))}")
    if st.session_state.get("match_jd_ocr_text"):
        st.success("图片JD已识别。原文已隐藏，评分后可在“岗位信息”模块查看。")
        if st.button("清除图片识别结果", use_container_width=True):
            st.session_state.pop("match_jd_ocr_text", None)
            st.session_state.pop("match_jd_ocr_error", None)
            st.rerun()
    return st.session_state.get("match_jd_ocr_text", "").strip()


st.markdown("""
<section class="hero"><div class="eyebrow">For Students & Early-Career Candidates</div><h1>让每一份简历，更接近理想岗位。</h1><p>面向校招与实习求职者：上传现有简历和目标岗位，在一次流程内完成证据化匹配、定制修改、人工确认与文件导出，减少反复比对和改写时间。</p><div class="trust-row"><span>✓ 不编造经历</span><span>✓ 显示匹配证据</span><span>✓ 支持人工调整</span><span>✓ Word / PDF 导出</span></div></section>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## JobPilot"); st.caption("你的 AI 简历工作台"); st.markdown("---")
    if get_api_key():
        st.success("AI服务已配置")
    else:
        st.error("AI服务未配置，请联系管理员")
    st.markdown("**隐私与AI说明**")
    st.caption("简历和JD会发送至DeepSeek API处理。本应用不主动持久化上传文件。AI结果仅供求职材料优化，下载前必须人工核对。")
    privacy_consent = st.checkbox(
        "我已阅读并同意上述处理方式",
        key="privacy_consent",
    )
    with st.expander("产品能力边界"):
        st.markdown("- 能做：匹配分析、证据定位、简历改写、英文翻译和导出。\n- 不能做：验证经历真实性、保证招聘结果、补造缺失经验。\n- 信息不足：标记为待确认，不写入简历正文。")
    with st.expander("清空本次数据"):
        clear_confirmed = st.checkbox("确认清空上传内容、分析和成稿", key="clear_confirmed")
        if st.button("确认清空", use_container_width=True, disabled=not clear_confirmed):
            track_event("workspace_cleared")
            for key in list(st.session_state.keys()):
                if key.startswith(("match_", "english_")):
                    st.session_state.pop(key, None)
            st.session_state.clear_confirmed = False
            st.rerun()

match_tab, english_tab = st.tabs(["01  JD匹配与定制", "02  中文简历转英文"])

with match_tab:
    st.markdown('<div class="step-title">上传简历并填写岗位 JD</div><div class="step-sub">先获得证据化匹配评分，再决定是否生成针对该岗位的定制版本。</div>', unsafe_allow_html=True)
    render_flow_steps(4 if st.session_state.get("match_revised") else 3 if st.session_state.get("match_analysis") else 1)
    left, right = st.columns(2, gap="large")
    with left:
        with st.container(border=True):
            st.markdown("### ① 上传简历")
            st.caption("PDF、DOCX、TXT 或 Markdown，最大 10MB")
            match_file = st.file_uploader(
                "选择简历文件", type=["pdf", "docx", "txt", "md"],
                key="match_resume_file", label_visibility="collapsed",
            )
    with right:
        with st.container(border=True):
            st.markdown("### ② 添加图片 JD（可选）")
            st.caption("拖拽截图或从剪贴板粘贴，识别原文默认隐藏")
            image_jd = render_jd_image_input()
    st.markdown("### ③ 输入文字 JD（可选）")
    st.caption("可单独使用文字，也可以与图片识别结果合并分析。")
    typed_jd = st.text_area(
        "输入岗位JD", height=135, key="match_jd_text", label_visibility="collapsed",
        placeholder="粘贴岗位职责、任职要求；如果已经识别图片，这里可以留空……",
    ).strip()
    match_jd = "\n".join(part for part in (typed_jd, image_jd) if part)
    can_analyze = bool(match_file and match_jd.strip() and privacy_consent and get_api_key())
    if not privacy_consent:
        st.caption("开始分析前，请先在左侧确认隐私与数据处理说明。")
    analyze_label = "重新评分" if st.session_state.get("match_analysis") else "开始匹配度评分"
    if st.button(analyze_label, type="primary", use_container_width=True, disabled=not can_analyze):
        try:
            track_event("match_analysis_started", jd_source="image_and_or_text")
            source = extract_text_bytes(match_file.getvalue(), match_file.name)
            with st.spinner("正在解析岗位要求并核对简历证据……"):
                analysis = get_agent().analyze_resume_text(source, match_jd)
            st.session_state.match_analysis, st.session_state.match_source, st.session_state.match_jd_used = analysis, source, match_jd
            for key in ("match_revised", "match_revised_history"):
                st.session_state.pop(key, None)
            track_event("match_analysis_completed", score=analysis.get("match_result", {}).get("match_score"))
            st.rerun()
        except Exception as exc:
            track_event("match_analysis_failed", error_type=type(exc).__name__)
            st.error(f"分析失败：{friendly_error(exc)}")

    analysis = st.session_state.get("match_analysis")
    if not analysis:
        st.info("上传简历并提供文字或图片JD后，系统将展示四维评分、证据、缺口和修改建议。输入不足或无法解析时会保留材料并提示修正。")
    if analysis:
        job, match = analysis.get("job_info", {}), analysis.get("match_result", {})
        score, breakdown = match.get("match_score", 0), match.get("score_breakdown", {})
        st.info("AI评分仅基于本次简历和JD中的明确证据；“待确认”表示材料不足，不等于用户不具备该能力。")
        st.markdown('<div class="step-title">匹配结果</div>', unsafe_allow_html=True)
        score_col, summary_col = st.columns([1, 2.6], gap="large")
        score_col.metric("简历匹配度", f"{score}/100"); score_col.progress(max(0, min(score, 100)) / 100)
        summary_col.markdown(f"### {job.get('job_title') or '目标岗位'}"); summary_col.write(match.get("summary") or "暂无总结")
        st.markdown("#### 四维评分")
        cols = st.columns(4, gap="medium")
        dimensions = [
            ("核心要求", "core_requirements", 40, "岗位硬性要求"),
            ("相关经历", "relevant_experience", 30, "实习与项目证据"),
            ("技能工具", "skills_tools", 20, "技能和工具覆盖"),
            ("加分项", "bonus_items", 10, "岗位偏好与亮点"),
        ]
        for col, (label, key, maximum, description) in zip(cols, dimensions):
            value = max(0, min(breakdown.get(key, 0), maximum))
            col.metric(label, f"{value}/{maximum}")
            col.progress(value / maximum)
            col.caption(description)
        evidence_tab, gap_tab, advice_tab, job_tab = st.tabs(["匹配证据", "缺口诊断", "修改建议", "岗位信息"])
        with evidence_tab:
            a, b = st.columns(2)
            with a: render_items("明确匹配", match.get("strong_matches", []), "✓")
            with b: render_items("部分匹配", match.get("partial_matches", []), "◐")
        with gap_tab:
            a, b, c = st.columns(3)
            with a: render_items("关键词缺口", match.get("keyword_gaps", []), "⌕")
            with b: render_items("能力差距", match.get("gaps", []), "△")
            with c: render_items("待确认信息", match.get("unknowns", []), "?")
        with advice_tab:
            a, b = st.columns(2)
            with a: render_items("简历修改建议", match.get("improvement_suggestions", []), "✎")
            with b: render_items("优先行动", match.get("priority_actions", []), "→")
        with job_tab:
            top = st.columns(3)
            top[0].metric("岗位名称", job.get("job_title") or "未识别")
            top[1].metric("岗位类型", job.get("job_type") or "未说明")
            top[2].metric("经验要求", job.get("experience_level") or "未说明")
            a, b = st.columns(2)
            with a:
                render_items("核心职责", job.get("responsibilities", []), "▣")
                render_items("必备技能", job.get("required_skills", []), "◆")
            with b:
                render_items("加分技能", job.get("bonus_skills", []), "+")
                render_items("岗位关键词", job.get("keywords", []), "#")
            if st.session_state.get("match_jd_ocr_text"):
                with st.expander("查看图片识别到的JD原文"):
                    st.text(st.session_state.match_jd_ocr_text)
        render_feedback("match_analysis")
        with st.expander("下载完整分析报告"):
            a, b = st.columns(2)
            a.download_button("Markdown 报告", build_markdown_report(analysis).encode("utf-8"), "jobpilot_analysis.md", use_container_width=True)
            b.download_button("JSON 数据", build_json_report(analysis).encode("utf-8"), "jobpilot_analysis.json", use_container_width=True)
        if not st.session_state.get("match_revised"):
            st.markdown('<div class="step-title">是否一键生成定制简历？</div><div class="step-sub">保留完整主要经历，通过排序和篇幅分配重点匹配JD；缺少证据的要求不会进入正文。</div>', unsafe_allow_html=True)
            if st.button("一键修改并生成可下载简历", type="primary", use_container_width=True):
                try:
                    track_event("tailored_resume_started")
                    with st.spinner("正在生成JD定制版本……"):
                        revised = get_agent().revise_resume(st.session_state.match_source, st.session_state.match_jd_used, analysis)
                        st.session_state.match_revised = attach_exports(revised, "zh")
                    track_event("tailored_resume_completed")
                    st.rerun()
                except Exception as exc:
                    track_event("tailored_resume_failed", error_type=type(exc).__name__)
                    st.error(f"生成失败：{friendly_error(exc)}")
        render_resume_adjuster("match_revised", "match_source", "zh")

with english_tab:
    st.markdown('<div class="step-title">将中文简历转换为专业英文版本</div><div class="step-sub">准确翻译、统一商务表达，并自动采用无照片、ATS友好的外企简历版式。</div>', unsafe_allow_html=True)
    render_flow_steps(4 if st.session_state.get("english_result") else 1)
    english_file = st.file_uploader("上传中文简历", type=["pdf", "docx", "txt", "md"], key="english_resume_file")
    if st.button("生成英文简历", type="primary", use_container_width=True, disabled=english_file is None or not privacy_consent or not get_api_key()):
        try:
            track_event("english_resume_started")
            source = extract_text_bytes(english_file.getvalue(), english_file.name)
            with st.spinner("正在翻译并按外企招聘习惯整理……"):
                st.session_state.english_result = attach_exports(get_agent().translate_resume(source), "en")
            st.session_state.english_source, st.session_state.english_result_history = source, []
            track_event("english_resume_completed")
            st.rerun()
        except Exception as exc:
            track_event("english_resume_failed", error_type=type(exc).__name__)
            st.error(f"翻译失败：{friendly_error(exc)}")
    translated = st.session_state.get("english_result")
    if translated:
        removed = translated.get("removed_personal_information", [])
        if removed:
            st.info("英文版已移除的非必要个人信息：" + "、".join(removed))
        if translated.get("translation_notes"):
            with st.expander("查看翻译与本地化说明"):
                for note in translated["translation_notes"]:
                    st.markdown(f"- {note}")
        render_resume_adjuster("english_result", "english_source", "en")
