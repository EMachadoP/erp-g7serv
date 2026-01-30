from django import template

register = template.Library()

@register.filter
def currency(value):
    """
    Format a number as Brazilian currency: 1.234,56
    """
    if value is None or value == '':
        return ''
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value
        
    # Format: 1,234.56
    s = f"{value:,.2f}"
    # Swap: 1.234,56
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')
