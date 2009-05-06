from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from mainapp.models import FaqEntry
from django.template import Context, RequestContext


def show( request, slug ):
    faq = get_object_or_404(FaqEntry, slug=slug)
    return render_to_response("faq/show.html",
                {"faq_entry":faq },
                 context_instance=RequestContext(request))

