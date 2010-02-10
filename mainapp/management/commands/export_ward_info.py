from mainapp.models import Ward,City,Councillor
from optparse import make_option
from django.core.management.base import BaseCommand,CommandError
from unicodewriter import UnicodeWriter


class Command(BaseCommand):
    help = 'Export ward names and councillors in a CVS format for a given city'
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
        csv = UnicodeWriter(file)
        
        for city_name in options['city'].split(','):
            print city_name
            city = City.objects.get(name=city_name)
            wards = Ward.objects.filter(city=city)
            for ward in wards:
                row = [ city.name, ward.name, ward.councillor.first_name, ward.councillor.last_name, ward.councillor.email]
                csv.writerow(row)

