from collab.settings import AUTH_USER_MODEL
from django.core.urlresolvers import reverse
from django.db import models

from core.notifications.models import Notification
from core.notifications.email import EmailInfo

NOUN = {
            'serve': 'Service',
            'lead': 'Leadership',
            'innovate': 'Innovation',
        }


class Praise(models.Model):
    recipient = models.ForeignKey('core.Person', related_name='recepient')
    praise_nominator = models.ForeignKey(AUTH_USER_MODEL)
    cfpb_value = models.CharField(max_length=100)
    reason = models.TextField()
    date_added = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):

        url = reverse('staff_directory:show_thanks', args=())
        email_info = EmailInfo(
            subject="You were thanked in the staff directory!",
            text_template='staff_directory/email/user_thanked.txt',
            html_template='staff_directory/email/user_thanked.html',
            to_address=self.recipient.user.email,
        )

        # Notify recipient
        url = reverse('staff_directory:person', args=(self.recipient.user.person.stub,))
        title ="%s thanked you for %s" %\
            (self.praise_nominator.person.full_name,
                NOUN[self.cfpb_value])
        Notification.set_notification(self.praise_nominator,
            self.praise_nominator, "thanked", self, self.recipient.user,
                title, url, email_info)

        return super(Praise, self).save(*args, **kwargs)
