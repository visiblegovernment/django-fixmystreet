from django.conf import settings

def widget(request):
    extra_context = {}
    if hasattr(request,'base_template'):
        base = request.base_template
    else: 
        base = 'website_base.html'  
    extra_context['base_template'] = base
    if hasattr(request,'api_key'):
        extra_context['organization'] = str(request.api_key.organization)
    else:
        extra_context['organization'] = 'FixMyStreet.ca'
        
    if hasattr(request,'host_url'):
        extra_context['host'] = request.host_url
    return extra_context