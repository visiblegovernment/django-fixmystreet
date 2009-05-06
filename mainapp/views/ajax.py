from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, RequestContext
from mainapp.models import ReportCategory, ReportCategoryClass

def category_desc(request,id):    
   return render_to_response("ajax/category_description.html",
                {"category": ReportCategory.objects.get(id=id),
                  },
                context_instance=RequestContext(request))