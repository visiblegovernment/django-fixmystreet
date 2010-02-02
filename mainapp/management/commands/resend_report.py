from mainapp.models import Report,ReportUpdate
from optparse import make_option
import csv
from django.core.management.base import BaseCommand,CommandError

class Command(BaseCommand):
    help = 'Resend original notification email for a particular report'
    args = 'report_id'

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError("a report ID must be supplied")
        report_id = args[0]
        try:
            report = Report.objects.get(id=report_id)
        except Exception,e:
            raise CommandError("there is no report with id %s in the database." % report_id )
        report.first_update().notify_on_new()
        