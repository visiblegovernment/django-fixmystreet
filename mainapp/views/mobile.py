from contrib.django_restapi.model_resource import Collection
from contrib.django_restapi.responder import JSONResponder, XMLResponder
from django.contrib.gis.geos import fromstr
from django.contrib.gis.measure import D
from django.forms.util import ErrorDict

from mainapp.models import Report
from mainapp import search


class InputValidationException(Exception):
    pass

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
            except InputValidationException, e:
                errors = ErrorDict({'info': [str(e)]})
                error_code = 412
        else:
            error_code = 415
            errors = ErrorDict(
                {'info': ['Requested content type "%s" not available!' %format]})
        # Using the last used responder to return error
        return self.responder.error(request, error_code, errors)


class CreateReportApi(RestCollection):

    def create(self, request, *args, **kwargs):
    #
    # Create a New Report
    #
        form = request.method == 'POST' and forms.ReportForm(request.POST) or forms.ReportForm()
        if request.method == 'POST' and form.is_valid():
            # lon = request.GET.get("lon")
            #lat = request.GET.get("lat")
            #address = request.GET.get("q")

            #report = form.save()
            if report:
                return HttpResponseCreated(request, request.build_absolute_uri())
            return self.render('create.html', request, {'form': form})

class ReportRest(RestCollection):

    def read(self, request):
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
                try:
                    point_str = search.search_address(address, match_index, addrs)
                except search.SearchAddressDisambiguateError, e:
                    return self.responder.error(request, 412, ErrorDict({
                        'info': [str(e)],
                        'possible_addresses': addrs }))
            else:
                raise InputValidationException('Must supply either a `q`, `lat` `lon`, or a report `id`')

            radius = float(request.GET.get('r', 4))
            pnt = fromstr(point_str, srid=4326)
            reports = Report.objects.filter(is_confirmed = True,point__distance_lte=(pnt,D(km=radius))).distance(pnt).order_by('distance')

        return self.responder.list(request, reports)

reports_rest = ReportRest(
    queryset=Report.objects.all(),
    permitted_methods = ('GET', 'POST'),
#     expose_fields = ('id','point'),
)

report_create = CreateReportApi(
    queryset=Report.objects.all(),
    permitted_methods = ('GET', 'POST'),
#     expose_fields = ('id','point'),
)