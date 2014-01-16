from core.models import Person
from core.utils import json_response
from django.http import HttpResponseRedirect


def registration_required(f):
    def wrap(request, *args, **kwargs):
        # check to see if user has registered
        try:
            request.user.get_profile()
            return f(request, *args, **kwargs)
        except Exception as e:
            raise e
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def user_allows_tagging(f):
    def wrap(request, *args, **kwargs):
        person = Person.objects.get(stub=request.POST.get('person_stub'))

        if person.user == request.user or person.allow_tagging:
            return f(request, *args, **kwargs)
        else:
            errMsg = person.user.first_name + " " + person.user.last_name + " has chosen not to allow tagging."
            return json_response({'error': errMsg})

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap
