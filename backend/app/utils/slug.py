import re


def generate_slug(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s가-힣-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug[:200] if slug else "untitled"
