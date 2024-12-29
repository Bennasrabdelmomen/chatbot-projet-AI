def enforce_html_structure(content):
    """
    Ensure that the response content is properly wrapped in HTML tags.
    For code snippets, wrap in <pre><code>...</code></pre>.
    Remove unnecessary markdown syntax (e.g., ```).
    """
    if "```" in content:
        code_content = content.replace("```html", "").replace("```", "").strip()
        return f"<pre><code>{code_content}</code></pre>"

    if not content.startswith("<") or not content.endswith(">"):
        return f"<p>{content}</p>"

    return content
