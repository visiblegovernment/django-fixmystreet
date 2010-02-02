from mainapp.models import City,EmailRule
from optparse import make_option
import csv
from django.core.management.base import BaseCommand,CommandError

class Command(BaseCommand):
    help = 'Export email rules for particular city/cities'
    option_list = BaseCommand.option_list + (
        make_option('--city', '-c', dest='city',help='cityname[,cityname]'),
        make_option('--file', '-f', dest='file',help='name of output file'),

    )

    def handle(self, *args, **options):
        if not options.has_key('file'):
            raise CommandError("An output filename must be specified with -f=")
        if not options.has_key('city'):
            raise CommandError("At least one city must be specified with -c=")
        
        file = open(options['file'],'w')
        
        for city_name in options['city'].split(','):
            try:
                city = City.objects.get(name=city_name)
            except:
                raise CommandError("city %s not found in database."% city_name)
            
            rules = EmailRule.objects.filter(city=city)
            for rule in rules:
                file.write(str(rule) + "\n")
        
        file.close()