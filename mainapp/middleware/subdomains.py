"""
    Used subdomain middleware example from here:
    http://thingsilearned.com/2009/01/05/using-subdomains-in-django/
    
    adds the following to the request:
     - host: the HTTP_HOST preceded by http:// - used when formatting 
             links for outgoing emails.
     - subdomain: can be used to identify a city, eg.
             toronto.fixmystreet.ca
    
    NOTE: there may be login issues across sub-domains when user
    logins are supported
"""

import settings

class SubdomainMiddleware:
        def process_request(self, request):
            """Parse out the subdomain from the request"""
            request.subdomain = None
            host_domain = request.META.get('HTTP_HOST', None)
            if host_domain:
                request.host_url = 'http://' + host_domain
                host_s = host_domain.replace('www.', '').split('.')
                if len(host_s) > 2:
                    request.subdomain = ''.join(host_s[:-2])
            else:
                # true for test cases.
                request.host_url = settings.SITE_URL
 