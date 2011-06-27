from contrib.django_restapi.model_resource import Collection
from contrib.django_restapi.responder import JSONResponder, XMLResponder
from django.contrib.gis.geos import fromstr
from django.contrib.gis.measure import D
from django.forms.util import ErrorDict
from mainapp.models import Report,ReportCategory
from mainapp import search
from mainapp.views.reports.main import create_report
import md5
import binascii
import settings
from django.core import serializers
from django.http import HttpResponse, HttpResponseBadRequest
from django.db import models


class InputValidationException(Exception):
    pass

class InvalidAPIKey(Exception):
    pass

class MobileReportAPI(object):
    
    EXPOSE_FIELDS = ('id','point', 'title','desc','author','email_sent_to','created_at','is_fixed')

    FORIEGN_TO_LOCAL_KEYS = {    'customer_email':'email',
                                 'customer_phone':'phone',
                                 'description': 'desc',
                                 'category': 'category_id'
                            }
    
    def get(self,request):
        ids = request.GET.getlist("id")
        if ids:
            try:
                ids = [int(id) for id in ids]
            except (TypeError, ValueError), e:
                raise InputValidationException(str(e))
            reports = Report.objects.filter(id__in = ids)
            # process ids right now
        else:
            lon = request.GET.get("lon")
            lat = request.GET.get("lat")
            address = request.GET.get("q")
            if lat and lon:
                point_str = "POINT(%s %s)" %(lon, lat)
            elif address:
                addrs = []
                match_index = int(request.GET.get('index', -1))
                point_str = search.search_address(address, match_index, addrs)
            else:
                raise InputValidationException('Must supply either a `q`, `lat` `lon`, or a report `id`')

            radius = float(request.GET.get('r', 4))
            pnt = fromstr(point_str, srid=4326)
            reports = Report.objects.filter(is_confirmed = True,point__distance_lte=(pnt,D(km=radius))).distance(pnt).order_by('distance')[:100]
            return( reports ) 
        
    def post(self,request):
        request.POST = MobileReportAPI._transform_params(request.POST)

        if not request.POST.has_key('device_id'):
            raise InputValidationException('General Service Error: No device_id')

        if not MobileReportAPI._nonce_ok(request):
            raise InvalidAPIKey('Invalid API Key')
 
        # we're good.        
        report = create_report(request,True)
        if not report:
            # some issue with our form input.  Does this need to be more detailed?
            raise InputValidationException('General Service Error: bad input')
        return( Report.objects.filter(pk=report.id) )
    
    def make_response(self,format,models = [],fields= None,status=200):
        mimetype = 'application/%s'%format
        data = serializers.serialize(format, models, fields=fields)
        return HttpResponse(data,mimetype=mimetype,status=status)
    
    @staticmethod    
    def _nonce_ok(request):
        timestamp = request.POST.get('timestamp')
        email = request.POST.get('email')
        nonce = request.POST.get('api_key')
        seed = '%s:%s:%s' % ( email,timestamp,settings.MOBILE_SECURE_KEY )
        m = md5.new( seed )
        compare_nonce = binascii.b2a_base64(m.digest())
        return( compare_nonce == nonce)
    
    @staticmethod
    def _transform_params(params):
        for theirkey,ourkey in MobileReportAPI.FORIEGN_TO_LOCAL_KEYS.items():
            if params.has_key(theirkey):
                params[ ourkey ] = params[ theirkey ]
                del(params[theirkey])
        
        # combine first and last names.
        if params.has_key('first_name') or params.has_key('last_name'):
            if params.has_key('first_name') and params.has_key('last_name'):
                params['author'] = params.get('first_name') + " " + params.get('last_name')
            else:
                params['author'] = params.get('first_name',params.get('last_name'))
            del(params['first_name'])
            del(params['last_name'])
                
        return( params )


class RestCollection(Collection):
    ''' Subclasses Collection to provide multiple responders '''
    def __init__(self, queryset, responders=None, **kwargs):
        '''
        Replaces the responder in Collection.__init__ with responders, which
        maybe a list of responders or None. In the case of None, default
        responders are allocated to the colelction.

        See Collection.__init__ for more details
        '''
        if responders is None:
            responders = {
                'json'  : JSONResponder(),
                'xml'   :XMLResponder(),
            }
        self.responders = {}
        for k, r in responders.items():
            Collection.__init__(self, queryset, r, **kwargs)
            self.responders[k] = self.responder

    def __call__(self, request, format, *args, **kwargs):
        '''
        urls.py must contain .(?P<format>\w+) at the end of the url
        for rest resources, such that it would match one of the keys
        in self.responders
        '''
        error_code = 400
        errors = ErrorDict({'info': ["An error has occured"]})
        if format in self.responders:
            self.responder = self.responders[format]
            try:
                return Collection.__call__(self, request, *args, **kwargs)
            except search.SearchAddressDisambiguateError, e:
                return self.responder.error(request, 412, ErrorDict({
                    'info': [str(e)],
                    'possible_addresses': addrs }))

            except InputValidationException, e:
                errors = ErrorDict({'info': [str(e)]})
                error_code = 412
        else:
            error_code = 415
            errors = ErrorDict(
                {'info': ['Requested content type "%s" not available!' %format]})
        # Using the last used responder to return error
        return self.responder.error(request, error_code, errors)
    

class MobileReportRest(RestCollection):

    api = MobileReportAPI()
    
    def read(self, request):
        reports = self.api.get(request)
        return self.responder.list(request, reports)

    def create(self, request, *args, **kwargs):
        report = self.api.post(request)
        return self.responder.list(request, report )

            

# These use the django-rest-api library.
mobile_report_rest = MobileReportRest(
    queryset=Report.objects.all(),
    permitted_methods = ['GET', 'POST'],
    expose_fields = MobileReportAPI.EXPOSE_FIELDS
)

json_poll_resource = Collection(
    queryset = ReportCategory.objects.all(),
    expose_fields = ('id', 'name_en', 'name_fr'),
    #permitted_methods = ('GET'),
    responder = JSONResponder()
)

# These classes do not use the django-rest-api library

class MobileReportAPIError(models.Model):
    EXPOSE_FIELDS = ('error',)
    error = models.CharField(max_length=255)
    
def mobile_reports( request, format ):
    api = MobileReportAPI()
    supported_formats = [ 'xml','json' ]
    if not format in supported_formats:
        return( HttpResponse('Requested content type "%s" not available.'%format,status=415))         
    try:
        if request.method == "POST":
            to_serialize = api.post(request)
        else:
            to_serialize = api.get(request) 
        return( api.make_response(format,to_serialize,MobileReportAPIError.EXPOSE_FIELDS ) )
    except Exception, e:
        to_serialize = [ MobileReportAPIError(error=str(e)) ]
        return( api.make_response(format,to_serialize,MobileReportAPIError.EXPOSE_FIELDS, status=412 ) )
 
