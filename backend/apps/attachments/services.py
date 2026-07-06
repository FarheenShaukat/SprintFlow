def build_supabase_storage_url(file_path: str, *, bucket: str = "task-attachments", supabase_url: str = "") -> str:
    if file_path.startswith("http"):
        return file_path
    base = supabase_url.rstrip("/")
    return f"{base}/storage/v1/object/public/{bucket}/{file_path.lstrip('/')}" if base else file_path
