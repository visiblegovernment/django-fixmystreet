"""
    Subdomain middleware from here:
    http://thingsilearned.com/2009/01/05/using-subdomains-in-django/
    
    NOTE: there may be login issues across sub-domains when user
    logins are supported
"""

class SubdomainMiddleware:
        def process_request(self, request):
            """Parse out the subdomain from the request"""
            request.subdomain = None
            host = request.META.get('HTTP_HOST', '')
            host_s = host.replace('www.', '').split('.')
            if len(host_s) > 2:
                request.subdomain = ''.join(host_s[:-2])