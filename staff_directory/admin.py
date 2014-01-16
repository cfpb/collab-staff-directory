from django.contrib import admin
from staff_directory.models import Praise

from core.actions import export_as_csv_action



class PraiseAdmin(admin.ModelAdmin):
    list_display = ('date_added', 'recipient', 'praise_nominator', 'cfpb_value')
    actions = [export_as_csv_action("CSV Export",
                                    fields=['date_added',
                                            'recipient',
                                            'praise_nominator',
                                            'cfpb_value',
                                            'reason'])]

admin.site.register(Praise, PraiseAdmin)
