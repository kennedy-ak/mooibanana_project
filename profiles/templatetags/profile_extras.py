# profiles/templatetags/profile_extras.py
from django import template
from django.http import QueryDict

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    return dictionary.get(key, 0)

@register.filter
def lookup(choices, key):
    """Look up choice display value by key"""
    if not key:
        return ''
    for choice_key, choice_value in choices:
        if choice_key == key:
            return choice_value
    return key

@register.simple_tag
def url_replace(request, field, value):
    """Replace a GET parameter while preserving others"""
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()
