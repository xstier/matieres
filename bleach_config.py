# utils/bleach_config.py

allowed_tags = [
    'b', 'i', 'em', 'strong', 'u', 'br', 'p', 'div', 'span',
    'input', 'select', 'option', 'textarea', 'label', 'ul', 'ol', 'li'
]

allowed_attributes = {
    '*': ['class', 'style'],
    'input': ['type', 'class', 'style', 'placeholder', 'value', 'name'],
    'select': ['class', 'style', 'name'],
    'option': ['value', 'selected'],
    'textarea': ['class', 'style', 'name', 'rows', 'cols', 'placeholder'],
    #'div': ['class', 'style'],
    'span': ['class', 'style'],
    'p': ['class', 'style'],
    'label': ['for', 'class', 'style']
}
