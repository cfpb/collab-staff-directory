from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(isSafe=True)
@stringfilter

# Removes a tag slug from a selected_tags parameter when supplied as a URL arg
def remove_tag(value, arg):
    """Removes a tag from the selected tags string
        If more than one tag (contains /) then check if
        first or follow-on before removing
    """

    if "/" in value:
        if ("/" + arg) in value:
            return value.replace(("/" + arg), '')
        else:
            return value.replace((arg + "/"), '')

