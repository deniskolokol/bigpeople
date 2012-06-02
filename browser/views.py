from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.conf import settings as django_conf_settings
from browser.forms import LoginForm
from browser.decorators import is_screenwriter, is_interpreter
from browser.utils import get_error_descr
import settings


def usr_login(request):
    """User login process
    """
        
    def error_handle(error, lang=None):
        if not lang:
            lang= settings.DEFAULT_LANG
        form= LoginForm()
        return render_to_response('login.html',
            {'error': get_error_descr(error, lang), 'form': form},
            context_instance=RequestContext(request))

    if request.method== 'POST': # If the form has been submitted
        form= LoginForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            username= request.POST['username']
            password= request.POST['password']
            user= authenticate(username=username, password=password)
            if user is not None:
                if user.is_active: # Redirect to a success page.
                    login(request, user)
                    # return redirect(reverse('celebrity_list'))
                    return redirect(django_conf_settings.LOGIN_REDIRECT_URL)
                else: # Return a 'disabled account' error message
                    error= 'auth_user_disabled'
                    return error_handle(error)
            else: 
                error= 'auth_invalid_login'
                return error_handle(error)
        else:
            error= 'auth_no_user'
            return error_handle(error)
    else:
        form= LoginForm() # An unbound form
        return render_to_response('login.html', {'form': form},
            context_instance=RequestContext(request))


def usr_logout(request):
    """Log user out
    """
    logout(request)
    return redirect(reverse('usr_login'))

@login_required
def usr_redirect(request):
    """Redirect user after login to a proper page
    """
    if is_screenwriter(request.user):
        return redirect(reverse('celebrity_list'))
    elif is_interpreter(request.user):
        return redirect(reverse('script_list'))
    else:
        return redirect(reverse('usr_login'))
    
