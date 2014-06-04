from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(isSafe=True)
@stringfilter

# Removes a tag slug from a selected_tags parameter when supplied as a URL arg
def remove_tag(value, arg):
    """Removes a tag from the selected tags string"""
    print "Argument: "
    print arg
    print "Value: "
    print value

    # If you are working with multiple tags, make sure to include the trailing slash
    # when you remove the tag
    if "/" in value:
        if ("/" + arg) in value:
            return value.replace(("/" + arg), '')
        else:
            return value.replace((arg + "/"), '')

