from pathlib import Path
from io import BytesIO


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_EXTRACTED_CHARS = 80_000


def _clean_and_validate(text: str) -> str:
    cleaned = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    if not cleaned:
        raise ValueError("未从简历文件中提取到文本；扫描版PDF需要先进行OCR。")
    if len(cleaned) > MAX_EXTRACTED_CHARS:
        raise ValueError(f"简历文本超过{MAX_EXTRACTED_CHARS}字符，请精简后重试。")
    return cleaned


def extract_text_bytes(data: bytes, filename: str) -> str:
    """Extract resume text directly from uploaded bytes without persisting the file."""
    if not data:
        raise ValueError("上传的简历文件为空。")
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("简历文件不能超过10MB。")

    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError("仅支持TXT、Markdown、PDF和DOCX简历。")

    if suffix in {".txt", ".md"}:
        text = data.decode("utf-8-sig")
    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("解析PDF需要安装pypdf。") from exc
        reader = PdfReader(BytesIO(data))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("解析DOCX需要安装python-docx。") from exc
        document = Document(BytesIO(data))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        table_cells = [cell.text for table in document.tables for row in table.rows for cell in row.cells]
        text = "\n".join(paragraphs + table_cells)

    return _clean_and_validate(text)


def extract_text(file_path: str | Path) -> str:
    """Extract resume text from TXT, Markdown, PDF, or DOCX files."""
    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"简历文件不存在：{path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"暂不支持{suffix or '无扩展名'}文件；支持TXT、Markdown、PDF和DOCX。"
        )

    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8-sig")
    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("解析PDF需要安装pypdf。") from exc
        reader = PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("解析DOCX需要安装python-docx。") from exc
        document = Document(str(path))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        table_cells = [cell.text for table in document.tables for row in table.rows for cell in row.cells]
        text = "\n".join(paragraphs + table_cells)

    return _clean_and_validate(text)
