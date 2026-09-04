import re
from bs4 import BeautifulSoup, Comment

# Allowed HTML elements for safe visual formatting
ALLOWED_TAGS = {
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code', 'div', 'em', 'h1',
    'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'li', 'ol', 'p', 'pre',
    'span', 'strong', 'table', 'tbody', 'td', 'th', 'thead', 'tr', 'u', 'ul',
    'header', 'footer', 'section', 'article', 'nav', 'main', 'mark', 'small'
}

# Allowed attributes per element
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel', 'class', 'id'],
    'img': ['src', 'alt', 'title', 'width', 'height', 'class', 'id'],
    '*': ['class', 'id', 'style']
}

# Dangerous URL schemes
DANGEROUS_SCHEMES = re.compile(r'^\s*(javascript|data|vbscript):', re.IGNORECASE)

def sanitize_html(raw_html: str) -> str:
    """
    Strips executable scripts, dangerous event attributes (onload/onerror),
    and unsafe URL schemes from HTML string.
    """
    if not raw_html:
        return ""

    soup = BeautifulSoup(raw_html, 'html.parser')

    # Remove HTML comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()


    # Remove forbidden tags entirely (including contents of <script>, <style>)
    FORBIDDEN_TAGS = ['script', 'style', 'iframe', 'object', 'embed', 'form', 'base', 'meta', 'link']
    for tag_name in FORBIDDEN_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Process all remaining elements
    for tag in soup.find_all(True):
        if tag.name not in ALLOWED_TAGS:
            # Unwrap tag but keep inner text
            tag.unwrap()
            continue

        # Filter attributes
        allowed_attrs_for_tag = ALLOWED_ATTRIBUTES.get(tag.name, []) + ALLOWED_ATTRIBUTES.get('*', [])
        attrs_to_remove = []

        for attr, value in list(tag.attrs.items()):
            attr_lower = attr.lower()
            # Strip any event handlers (on*)
            if attr_lower.startswith('on') or attr_lower not in allowed_attrs_for_tag:
                attrs_to_remove.append(attr)
                continue

            # Check URL values in href or src
            if attr_lower in ('href', 'src'):
                val_str = str(value)
                if DANGEROUS_SCHEMES.search(val_str):
                    attrs_to_remove.append(attr)

        for attr in attrs_to_remove:
            del tag[attr]

        # Enforce security attributes on external links
        if tag.name == 'a' and 'href' in tag.attrs:
            tag['rel'] = 'noopener noreferrer'
            tag['target'] = '_blank'

    return str(soup)
