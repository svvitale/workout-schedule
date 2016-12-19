from django.shortcuts import render
from django.utils.timezone import now, localtime
from django.views import View
import grequests
from datetime import date
from dateutil.parser import parse


class IndexView(View):
    DATE_FORMAT = '%m/%d/%Y'

    def schedule_url(self, club_id, requested_date):
        return 'http://schedule.24hourfitness.com/_services/Calendar/getClasses?clubid={}&startdate={}'\
            .format(club_id, requested_date.strftime(self.DATE_FORMAT))

    def get(self, request):

        if request.GET.get('date'):
            requested_date = parse(request.GET.get('date')).date()
        else:
            requested_date = localtime(now()).date()

        scheduled_classes = {}

        locations = {
            'Alameda': '00351',
            'Glendale': '00277',
            'Lowry': '00572',
            'Highlands': '00956'
        }

        sorted_location_names = sorted(locations)

        schedule_requests = [grequests.get(self.schedule_url(locations[name], requested_date))
                             for name in sorted_location_names]

        for location_idx, schedule_response in enumerate(grequests.map(schedule_requests)):
            for class_entry in schedule_response.json():

                class_datetime = parse(class_entry['StartTime'])
                class_entry['Location'] = sorted_location_names[location_idx]

                if class_datetime.date() == requested_date:
                    # Add class
                    if class_datetime.time() not in scheduled_classes:
                        scheduled_classes[class_datetime.time()] = {}

                    if class_entry['Location'] not in scheduled_classes[class_datetime.time()]:
                        scheduled_classes[class_datetime.time()][class_entry['Location']] = []

                    scheduled_classes[class_datetime.time()][class_entry['Location']].append(class_entry)

        return render(request, 'index.html', {
            'requested_date': requested_date.strftime(self.DATE_FORMAT),
            'scheduled_classes': sorted(scheduled_classes.items()),
            'location_names': sorted_location_names
        })
