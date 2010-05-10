from django.http import HttpResponseNotFound
from mainapp.models import ApiKey
import re

"""
    Subdomain Middleware should be before this in the stack.
"""

class WidgetMiddleware:
        
        def process_request(self, request):
            key = self.get_api_key(request)
            if not key: 
                return
                        
            try:
                key_entry = ApiKey.objects.get(key=key)
            except ApiKey.DoesNotExist:
                return( HttpResponseNotFound('API Key does not exist.' ) )
            
            if key_entry.type != ApiKey.WIDGET:
                return
            
            request.api_key = key_entry 
                       
            # set the subdomain with the right city name
            if key_entry.city:
                request.subdomain = key_entry.city.name.lower()
            
            # add the template name to the request.
            request.base_template = key_entry.template
            
            # override the host URL
            request.host_url = 'http://'+ key_entry.domain + key_entry.link_offset
                
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
                # make sure all generated local URLs also have their api_key,etc. params
                response.content = re.sub(r'a\s+href=["\'](/.*?)["\']>', r'a href="\1?api_key=%s">' % key, response.content)
                response.content = re.sub(r'action=(.*?)>', r'action=\1>\n<input type=hidden name="api_key" value="%s">\n' % key, response.content)
            return(response)