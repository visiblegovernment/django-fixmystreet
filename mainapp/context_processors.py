from django.conf import settings

def widget(request):
    extra_context = {}
    if hasattr(request,'base_template'):
        base = request.base_template
    else: 
        base = 'website_base.html'  
    extra_context['base_template'] = base
    if hasattr(request,'api_key'):
        extra_context['widget_org'] = str(request.api_key.organization)
        extra_context['widget_domain'] = str(request.api_key.domain)
    if hasattr(request,'host'):
        extra_context['host'] = request.host
    return extra_context