from django.shortcuts import render_to_response, get_object_or_404
from mainapp.models import Report
from mainapp.forms import ContactForm
from django.template import Context, RequestContext
from django.http import HttpResponseRedirect

import settings

def thanks(request): 
     return render_to_response("contact/thanks.html", {},
                context_instance=RequestContext(request))

def new(request):
    if request.method == 'POST':
        form = ContactForm(data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect("/contact/thanks")
    else:
        form = ContactForm()

    return render_to_response("contact/new.html",
                              { 'contact_form': form },
                              context_instance=RequestContext(request))
