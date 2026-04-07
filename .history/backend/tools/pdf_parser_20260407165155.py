"""PDF简历解析工具"""
import io
from PyPDF2 import PdfReader


def parse_pdf(file_content: bytes) -> str:
    """
    解析PDF文件，提取纯文本内容
    :param file_content: PDF文件的字节内容
    :return: 提取的文本内容
    """
    try:
        reader = PdfReader(io.BytesIO(file_content))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text.strip())
        
        full_text = "\n".join(text_parts)
        
        if not full_text.strip():
            raise ValueError("PDF文件内容为空或无法识别文本")
        
        return full_text
    except Exception as e:
        raise Exception(f"PDF解析失败: {str(e)}")


def parse_pdf_file(file_path: str) -> str:
    """
    从文件路径解析PDF
    :param file_path: PDF文件路径
    :return: 提取的文本内容
    """
    with open(file_path, "rb") as f:
        return parse_pdf(f.read())
