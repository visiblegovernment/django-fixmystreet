from mainapp.models import CityAdmin, City
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
        user = CityAdmin.objects.create_user(options['userid'], options['email'], city, options['password'] )
        if not user:
            print "error creating user"