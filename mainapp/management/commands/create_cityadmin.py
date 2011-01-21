from mainapp.models import UserProfile,City
from optparse import make_option
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand,CommandError

class Command(BaseCommand):
    help = 'Create a city administrator user'
    option_list = BaseCommand.option_list + (
        make_option('--city', '-c', dest='city',help='city'),
        make_option('--userid', '-u', dest='userid',help='userid'),
        make_option('--pwd', '-p', dest='password',help='password'),
        make_option('--email', '-e', dest='email',help='email'),
    )

    def handle(self, *args, **options):
        for option in self.option_list:
            if not options.has_key(option.dest):
                raise CommandError("%s must be specified" % (option.dest))
        city = City.objects.get(name=options['city'])
        user = User.objects.create_user(options['userid'], options['email'], options['password'] )
        user.is_staff = True
        city_admin = Group.objects.get(name='CityAdmins')
        user.groups.add(city_admin)
        user.save()
        UserProfile(user=user,city=city).save()