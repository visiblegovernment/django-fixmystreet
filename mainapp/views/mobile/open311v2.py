from django.contrib.gis.geos import fromstr
from django.contrib.gis.measure import D
from django.shortcuts import render,render_to_response, get_object_or_404
from django.template import Context, RequestContext
from django.http import HttpResponse, HttpResponseBadRequest
from mainapp.models import ApiKey,Report,ReportCategory,DictToPoint,City
from django.conf.urls.defaults import patterns, url, include
from mainapp.forms import ReportForm
from django.conf import settings
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
import re

class InvalidAPIKey(Exception):

    def __init__(self):
        super(InvalidAPIKey,self).__init__("Invalid api_key received -- can't proceed with create_request.")
    
class ApiKeyField(forms.fields.CharField):
    
    def __init__(self,required=True, widget=None, label=None,
                 initial=None, help_text=None, *args, **kwargs):
        super(ApiKeyField,self).__init__(required=required,widget=widget,label=label,initial=initial,help_text=help_text,*args,**kwargs)

    def clean(self, value):
        try:
            api_key = ApiKey.objects.get(key=value)
        except ObjectDoesNotExist:
            raise InvalidAPIKey()
        return api_key


class Open311ReportForm(ReportForm):

    service_code = forms.fields.CharField()
    description = forms.fields.CharField()
    first_name = forms.fields.CharField(required=False)
    last_name = forms.fields.CharField()
    api_key = ApiKeyField()
    
    class Meta:
        model = Report
        fields = ('service_code','description','lat','lon','title', 'category', 'photo','device_id','api_key')

    def __init__(self,data=None,files=None,initial=None, user=None):
        
        if data:
            data = data.copy() # can't modify request.POST directly
            data['desc'] = data.get('description','')
            data['category'] = data.get('service_code','1')
            data['author'] = (data.get('first_name','') + " "  + data.get('last_name','')).strip()
        super(Open311ReportForm,self).__init__(data,files, initial=initial,user=user)
        self.fields['device_id'].required = True
        self.fields['category'].required = False
        self.fields['title'].required = False
        self.update_form.fields['author'].required = False
        
    def _get_category(self):
        service_code = self.cleaned_data.get('service_code',None)
        if not service_code:
            return ''
        categories = ReportCategory.objects.filter(id=service_code)
        if len(categories) == 0:
            return None
        return(categories[0])
    
        
    def clean_title(self):
        data = self.cleaned_data.get('title',None)
        if data:
            return data        
        category = self._get_category()
        if not category:
            return ''
        return ('%s: %s' % (category.category_class.name,category.name))

    
class Open311v2Api(object):
    
    def __init__(self, content_type ):
        self.content_type = content_type 
                
    def report(self,request, report_id ):
        report = get_object_or_404(Report, id=report_id)
        return self._render_reports( request, [ report ])

    def reports(self,request):
        if request.method != "POST":
            reports = Report.objects.filter(is_confirmed=True)
            if request.GET.has_key('lat') and request.GET.has_key('lon'):
                pnt = DictToPoint( request.GET ).pnt()
                d = request.GET.get('r','2')
                reports = reports.filter(point__distance_lte=(pnt,D(km=d)))     
            if request.GET.has_key('start_date'):
                reports = reports.filter(created_at__gte=request.GET['start_date'])
            if request.GET.has_key('end_date'):
                reports = reports.filter(created_at__lte=request.GET['end_date'])  
            reports = reports.order_by('-created_at')[:1000]
            return self._render_reports(request, reports)
        else:
            # creating a new report
            report_form = Open311ReportForm( request.POST, request.FILES,user=request.user )
            try:
                if report_form.is_valid():
                    report = report_form.save()
                    if report:
                        return( self._render_reports(request, [ report ] ) )
                return( self._render_errors(request, report_form.all_errors()))
            except InvalidAPIKey, e:
                return render( request,
                        'open311/v2/_errors.%s' % (self.content_type),
                        { 'errors' : {'403' : str(e) } },
                        content_type = 'text/%s' % ( self.content_type ),
                        context_instance=RequestContext(request),
                        status = 403 )

    def services(self,request):
        city = None
        if request.GET.has_key('lat') and request.GET.has_key('lon'):
            ward = DictToPoint( request.GET ).ward()
            if not ward:
                return HttpResponse('lat/lon not supported',status=404)
            city = ward.city
        if request.GET.has_key('jurisdiction_id'):
            # expect format <city>_<province-abbrev>.fixmystreet.ca
            city = self._parse_jurisdiction(request.GET['jurisdiction_id'])
            if not city:
                return HttpResponse('jurisdiction_id provided not found',status=404)
        if not city:
            return HttpResponse('jurisdiction_id was not provided',status=400)
        
        categories = city.get_categories()

        return render_to_response('open311/v2/_services.%s' % (self.content_type),
                          { 'services' : categories },
                          mimetype = 'text/%s' % ( self.content_type ),
                          context_instance=RequestContext(request))
    
    def _parse_jurisdiction(self,jurisdiction):
        # expect format <city>_<province-abbrev>.fixmystreet.ca
        match = re.match(r"(\w+)_(\w+)\.fixmystreet\.ca",jurisdiction)
        if not match:
            return None
        city = get_object_or_404(City,name__iexact=match.group(1),province__abbrev__iexact=match.group(2))
        return city
    
    def _render_reports(self, request, reports):
        return render_to_response('open311/v2/_reports.%s' % (self.content_type),
                          { 'reports' : reports },
                          mimetype = 'text/%s' % ( self.content_type ),
                          context_instance=RequestContext(request))

    def _render_errors(self,request,errors):
        return render( request,
                       'open311/v2/_errors.%s' % (self.content_type),
                        { 'errors' : errors },
                          content_type = 'text/%s' % ( self.content_type ),
                          context_instance=RequestContext(request),
                          status = 400 )

    
    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^requests.%s$' % ( self.content_type ), self.reports,  {'SSL': ['POST']} ),
            url(r'^services.%s$' % ( self.content_type ), self.services ),
            url(r'^requests/(\d+).%s$' % ( self.content_type ),
                self.report),
            )
        return urlpatterns
    
    @property
    def urls(self):
        return self.get_urls(), 'open311v2', 'open311v2'
    
xml = Open311v2Api('xml')
