from mainapp.models import City,Ward,Councillor
from django.core.management.base import BaseCommand,CommandError

class Command(BaseCommand):
    help = 'Add \'city\' link to councillors in database, get rid of unlinked councillors'

    def handle(self, *args, **options):
        for councillor in Councillor.objects.all():
            # do we have a ward for this councillor?
            try:
                ward = Ward.objects.get(councillor=councillor)
                councillor.city = ward.city
                councillor.save()
                print "saving councillor %s %s (%s)" % (councillor.first_name,councillor.last_name,ward.city)
            except:
                print "deleting councillor %s %s" % (councillor.first_name,councillor.last_name)
                councillor.delete()