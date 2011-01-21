from mainapp.models import Ward,Councillor,EmailRule
from django.db.models.signals import post_syncdb
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

cityadmin_permission_names = [ 'Can change ward', 
                     'Can add email rule',
                     'Can change email rule',
                     'Can delete email rule',
                     'Can add councillor',
                     'Can change councillor',
                     'Can delete councillor' ]

def add_cityadmin_group_permissions(sender, **kwargs):
    if kwargs['app'].__name__ != 'mainapp.models':
        return
    
    city_admin,created = Group.objects.get_or_create(name='CityAdmins')
    for name in cityadmin_permission_names:
        permission = Permission.objects.get(name=name)
        city_admin.permissions.add(permission)
    city_admin.save()
    print "created %s cityadmin permission group" % kwargs['app'].__name__
    
post_syncdb.connect(add_cityadmin_group_permissions)
