from django.core.files.uploadedfile import UploadedFile


MAX_UPLOAD_SIZE = 10 * 1024 * 1024
SUPPORTED_TYPES = {
    "text/plain",
    "text/markdown",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def extract_uploaded_text(uploaded_file: UploadedFile | None) -> str:
    if not uploaded_file:
        return ""
    if uploaded_file.size > MAX_UPLOAD_SIZE:
        raise ValueError("File is too large. Maximum upload size is 10 MB.")

    content_type = uploaded_file.content_type or ""
    name = uploaded_file.name.lower()
    if content_type not in SUPPORTED_TYPES and not name.endswith((".txt", ".md", ".pdf", ".docx")):
        raise ValueError("Unsupported file type. Upload PDF, DOCX, TXT, or Markdown.")

    if name.endswith((".txt", ".md")) or content_type in {"text/plain", "text/markdown"}:
        return uploaded_file.read().decode("utf-8", errors="ignore")
    if name.endswith(".pdf") or content_type == "application/pdf":
        return _extract_pdf(uploaded_file)
    if name.endswith(".docx") or content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return _extract_docx(uploaded_file)
    raise ValueError("Unsupported file type. Upload PDF, DOCX, TXT, or Markdown.")


def _extract_pdf(uploaded_file: UploadedFile) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError("PDF extraction requires pypdf to be installed.") from exc
    reader = PdfReader(uploaded_file)
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def _extract_docx(uploaded_file: UploadedFile) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise ValueError("DOCX extraction requires python-docx to be installed.") from exc
    document = Document(uploaded_file)
    return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
