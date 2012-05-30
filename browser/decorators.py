"""A set of view decorators and checkiing functions,
related to authentication.
"""

from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User, Group
from permission_backend_nonrel.models import UserPermissionList

def _is_in_group(user, group_name):
    group= Group.objects.get(name=group_name)
    up= UserPermissionList.objects.filter(user=user)
    try:
        return True if unicode(group.id) in up[0].group_fk_list else False
    except:
        return False

def is_screenwriter(user):
    """Checks if the user is logged-in screenwriter.
    Param 'user' is the instance of django.contrib.auth.User
    or request.user
    """
    return _is_in_group(user, 'Screenwriter')

def is_interpreter(user):
    """Checks if the user is logged-in interpreter.
    """
    return _is_in_group(user, 'Interpreter')


screenwriter_required= user_passes_test(is_screenwriter)

interpreter_required= user_passes_test(is_interpreter)
