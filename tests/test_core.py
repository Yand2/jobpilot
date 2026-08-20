import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from agents.career_agent import CareerAgent
from skills.jd_analyzer import JDAnalyzer
from skills.resume_matcher import ResumeMatcher
from utils.file_parser import extract_text, extract_text_bytes
from utils.json_utils import parse_json_object
from utils.memory import Memory
from utils.report import build_markdown_report
from utils.ocr import extract_text_from_image
from utils.resume_export import build_docx_bytes, build_pdf_bytes


def response(content):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


class QueueCompletions:
    def __init__(self, contents):
        self.contents = list(contents)

    def create(self, **kwargs):
        return response(self.contents.pop(0))


class FakeClient:
    def __init__(self, contents):
        self.chat = SimpleNamespace(completions=QueueCompletions(contents))


class CoreTests(unittest.TestCase):
    def test_parse_fenced_json(self):
        self.assertEqual(parse_json_object('```json\n{"ok": true}\n```'), {"ok": True})

    def test_text_file_parser(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "resume.txt"
            path.write_text("AI产品项目", encoding="utf-8")
            self.assertEqual(extract_text(path), "AI产品项目")

    def test_uploaded_text_parser(self):
        self.assertEqual(extract_text_bytes("简历内容".encode("utf-8"), "resume.txt"), "简历内容")

    def test_memory_does_not_overwrite_with_empty_value(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            path.write_text('{"major": "信息管理"}', encoding="utf-8")
            memory = Memory(path)
            self.assertEqual(memory.update({"major": ""})["major"], "信息管理")

    def test_jd_and_match_schema(self):
        jd = {
            "job_title": "AI产品实习生", "company": "", "job_type": "实习",
            "responsibilities": [], "required_skills": ["需求分析"],
            "bonus_skills": [], "experience_level": "在校生", "keywords": ["AI产品"]
        }
        match = {
            "match_score": 70,
            "score_breakdown": {"core_requirements": 30, "relevant_experience": 20, "skills_tools": 15, "bonus_items": 5},
            "strong_matches": [], "partial_matches": [], "gaps": [], "unknowns": [],
            "keyword_gaps": [], "summary": "具备部分匹配能力", "priority_actions": [],
            "improvement_suggestions": []
        }
        client = FakeClient([json.dumps(jd, ensure_ascii=False), json.dumps(match, ensure_ascii=False)])
        job_info = JDAnalyzer(client).analyze("JD")
        result = ResumeMatcher(client).match(job_info, {"resume_text": "经历"})
        self.assertEqual(result["match_score"], 70)

    def test_rejects_invalid_score(self):
        invalid = {
            "match_score": 120,
            "score_breakdown": {"core_requirements": 40, "relevant_experience": 30, "skills_tools": 20, "bonus_items": 10},
            "strong_matches": [], "partial_matches": [], "gaps": [], "unknowns": [],
            "keyword_gaps": [], "summary": "", "priority_actions": [], "improvement_suggestions": []
        }
        with self.assertRaises(ValueError):
            ResumeMatcher(FakeClient([json.dumps(invalid)])).match({}, {})

    def test_markdown_report(self):
        result = {
            "job_info": {"job_title": "AI产品", "keywords": ["Agent"]},
            "match_result": {"match_score": 60, "summary": "部分匹配", "score_breakdown": {}}
        }
        report = build_markdown_report(result)
        self.assertIn("60/100", report)
        self.assertIn("AI产品", report)

    def test_ocr_rejects_empty_image(self):
        with self.assertRaises(ValueError):
            extract_text_from_image(b"")

    def test_resume_exports(self):
        resume = {
            "name": "测试用户",
            "contact": "test@example.com",
            "target_role": "AI产品",
            "summary": "具备需求分析和数据分析实践。",
            "sections": [{
                "title": "项目经历",
                "entries": [{
                    "heading": "JobPilot｜独立开发",
                    "date": "2026.08",
                    "bullets": ["使用Python搭建简历与岗位匹配分析工具。"],
                }],
            }],
        }
        docx_bytes = build_docx_bytes(resume)
        pdf_bytes = build_pdf_bytes(resume)
        self.assertTrue(docx_bytes.startswith(b"PK"))
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(docx_bytes), 10_000)
        self.assertGreater(len(pdf_bytes), 1_000)

    def test_revised_resume_numeric_evidence_guard(self):
        resume = {"name": "测试", "summary": "提升效率50%", "sections": []}
        CareerAgent._validate_numeric_evidence(resume, "原简历：提升效率50%")
        resume["summary"] = "提升效率80%"
        with self.assertRaises(ValueError):
            CareerAgent._validate_numeric_evidence(resume, "原简历：提升效率50%")

    def test_pdf_export_escapes_user_content(self):
        resume = {
            "name": "A&B <测试>", "contact": "a@example.com",
            "target_role": "AI产品", "summary": "Python & SQL",
            "sections": [],
        }
        self.assertTrue(build_pdf_bytes(resume).startswith(b"%PDF"))

    def test_translate_resume_schema_and_fact_guard(self):
        translated = {
            "resume": {
                "name": "Test User", "contact": "test@example.com",
                "target_role": "AI Product Intern", "summary": "Product candidate.",
                "sections": [{"title": "PROJECTS", "entries": [{
                    "heading": "JobPilot", "date": "2026",
                    "bullets": ["Built an AI matching agent."],
                }]}],
            },
            "translation_notes": [], "removed_personal_information": [],
            "missing_information": [],
        }
        agent = CareerAgent(FakeClient([json.dumps(translated)]))
        result = agent.translate_resume("Test User test@example.com JobPilot 2026 AI匹配Agent")
        self.assertEqual(result["resume"]["target_role"], "AI Product Intern")

    def test_english_resume_exports(self):
        resume = {
            "name": "Test User", "contact": "test@example.com",
            "target_role": "AI Product Intern", "summary": "Product candidate.",
            "sections": [],
        }
        self.assertTrue(build_docx_bytes(resume, language="en").startswith(b"PK"))
        self.assertTrue(build_pdf_bytes(resume, language="en").startswith(b"%PDF"))

    def test_one_page_content_guard(self):
        resume = {
            "sections": [{"title": "EXPERIENCE", "entries": [{
                "heading": "Role", "date": "", "bullets": ["Item"] * 13,
            }]}],
        }
        with self.assertRaises(ValueError):
            CareerAgent._validate_one_page_content(resume)

    def test_fit_resume_one_page(self):
        fitted = {
            "resume": {
                "name": "测试", "contact": "test@example.com", "target_role": "AI产品",
                "summary": "具备AI产品实践。", "sections": [{
                    "title": "项目经历", "entries": [{
                        "heading": "JobPilot", "date": "2026",
                        "bullets": ["开发AI简历匹配工具。"],
                    }],
                }],
            },
            "change_summary": ["压缩重复内容"], "missing_information": [],
        }
        agent = CareerAgent(FakeClient([json.dumps(fitted, ensure_ascii=False)]))
        result = agent.fit_resume_one_page(
            fitted["resume"], "测试 test@example.com AI产品 JobPilot 2026 开发AI简历匹配工具。",
        )
        self.assertEqual(result["resume"]["name"], "测试")
        self.assertEqual(len(result["resume"]["sections"]), 1)

    def test_compact_one_page_exports(self):
        resume = {
            "name": "测试", "contact": "test@example.com", "target_role": "AI产品",
            "summary": "具备AI产品实践。", "sections": [],
        }
        self.assertTrue(build_docx_bytes(resume, one_page=True).startswith(b"PK"))
        self.assertTrue(build_pdf_bytes(resume, one_page=True).startswith(b"%PDF"))

    def test_resume_adjustment_cannot_silently_drop_experience(self):
        before = {"sections": [{"entries": [{"heading": "A"}, {"heading": "B"}]}]}
        after = {"sections": [{"entries": [{"heading": "A"}]}]}
        with self.assertRaises(ValueError):
            CareerAgent._validate_entry_completeness(before, after)


if __name__ == "__main__":
    unittest.main()
