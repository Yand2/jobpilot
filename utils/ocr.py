from functools import lru_cache
from io import BytesIO

import numpy as np
from PIL import Image, ImageOps


MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000


@lru_cache(maxsize=1)
def _get_engine():
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        raise RuntimeError("图片OCR依赖未安装，请安装rapidocr-onnxruntime。") from exc
    return RapidOCR()


def extract_text_from_image(data: bytes) -> str:
    """Recognize Chinese/English text from an image with local OCR."""
    if not data:
        raise ValueError("图片内容为空。")
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("JD图片不能超过10MB。")

    try:
        image = Image.open(BytesIO(data))
        image.load()
    except Exception as exc:
        raise ValueError("无法读取该图片，请使用PNG、JPG或JPEG格式。") from exc

    if image.width * image.height > MAX_IMAGE_PIXELS:
        raise ValueError("图片像素过大，请裁剪或压缩后重试。")

    image = ImageOps.exif_transpose(image).convert("RGB")
    result, _ = _get_engine()(np.asarray(image))
    if not result:
        raise ValueError("没有识别到文字，请尝试更清晰的截图或直接粘贴JD文字。")

    lines = []
    for item in result:
        if len(item) >= 3 and isinstance(item[1], str):
            text = item[1].strip()
            score = float(item[2])
            if text and score >= 0.45:
                lines.append(text)
    if not lines:
        raise ValueError("OCR结果置信度过低，请更换清晰图片或直接粘贴JD文字。")
    return "\n".join(lines)
