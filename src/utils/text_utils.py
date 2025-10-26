def merge_text(description, content):
    desc, cont = description or "", content or ""
    return (desc + ". " + cont).strip()


def truncate_content(content, limit=300):
    if not content:
        return ""
    content = content.strip()
    if len(content) <= limit:
        return content
    truncated = content[:limit].rsplit(' ', 1)[0]
    return truncated.strip() + "..."
