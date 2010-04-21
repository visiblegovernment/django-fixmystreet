from django.shortcuts import get_object_or_404
from mainapp.models import ApiKey
import re

"""
    Subdomain Middleware should be before this in the stack.
"""

class WidgetMiddleware:
        
        def process_request(self, request):
            if not request.subdomain:
                return
            if request.subdomain != 'embedded':
                return
            key = self.get_api_key(request)
            if not key: 
                return
            key_entry = get_object_or_404(ApiKey,key=key)
            request.api_key = key_entry            
            # replace the subdomain with the right city name
            if key_entry.city:
                request.subdomain = key_entry.city.name.lower()
            
            # add the template name to the request.
            request.base_template = key_entry.template
                
        def get_api_key(self,request):
            return( request.POST.get('api_key',request.GET.get('api_key',None)) )

        def process_response(self,request,response):
            key = self.get_api_key(request)
            if not key:
                return( response )
                        
            # is the response a redirect?
            if response.status_code == 302:
                if re.search('\?', response['Location']) :
                    response['Location'] = '%s;api_key=%s' % (response['Location'], key)
                else:
                    response['Location'] = '%s?api_key=%s' % (response['Location'], key)                    
            else:
                # param_str = params.urlencode()
                # make sure all generated local URLs also have their api_key,etc. params
                response.content = re.sub(r'a\s+href=["\'](/.*?)["\']>', r'a href="\1?api_key=%s">' % key, response.content)
                response.content = re.sub(r'action=(.*?)>', r'action=\1>\n<input type=hidden name="api_key" value="%s">\n' % key, response.content)
            return(response)