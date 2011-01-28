from django import template
register = template.Library()

MENU_DEFS = { 'submit' : { 'exact': [ '/','/reports/new', '/search' ], 
                           'startswith':[],  
                           'exclude' : []
                         },
              'view' : { 'exact': [],
                         'startswith' : [ '/cities','/wards', '/reports' ],
                         'exclude':[ '/reports/new' ] }
            }

def is_match( path, pattern ):
    if MENU_DEFS.has_key(pattern):
        menudef = MENU_DEFS[pattern]
        if path in menudef[ 'exact' ]:
            return True
        for match in menudef['startswith']:
            if path.startswith(match) and not path in menudef['exclude']:
                   return True
        return False 
    if path.startswith(pattern):
        return True
    return False
    
@register.simple_tag
def fmsmenu_active(request, pattern ):
    if is_match(request.path, pattern ):
        return 'active'
    return ''


