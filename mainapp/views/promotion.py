from django.template import Context, RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from mainapp.models import Report, ReportUpdate


def show(request, promo_code):
    matchstr = "author LIKE '%%" + promo_code + "%%'"
    reports = Report.objects.filter(is_confirmed=True).extra(select={'match': matchstr }).order_by('created_at')[0:100]
    count = Report.objects.filter(author__contains=promo_code).count()
    return render_to_response("promotions/show.html",
                {   "reports": reports,
                    "promo_code":promo_code,
                    "count": count },
                context_instance=RequestContext(request))

