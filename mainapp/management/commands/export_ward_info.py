from mainapp.models import Ward,City,Councillor
from optparse import make_option
import csv
from django.core.management.base import BaseCommand,CommandError

class UnicodeWriter:
    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        self.writer = csv.writer(f, dialect=dialect, **kwds)
        self.encoding = encoding

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

class Command(BaseCommand):
    help = 'Export ward names and councillors in a CVS format for a given city'
    option_list = BaseCommand.option_list + (
        make_option('--city', '-c', dest='city',help='the city name'),
        make_option('--file', '-f', dest='file',help='name of output file'),

    )

    def handle(self, *args, **options):
        file = open(options['file'],'w')
        csv = UnicodeWriter(file)
        
        for city_name in options['city'].split(','):
            print city_name
            city = City.objects.get(name=city_name)
            wards = Ward.objects.filter(city=city)
            for ward in wards:
                row = [ city.name, ward.name, ward.councillor.first_name, ward.councillor.last_name]
                csv.writerow(row)