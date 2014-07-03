from django.core.urlresolvers import reverse
from django.test import TestCase

from exam.cases import Exam
from exam.decorators import before
from core.models import Person
from core.notifications.models import Notification
from staff_directory.models import Praise


class PraiseTest(Exam, TestCase):
    """
        Tests user adds Staff Thanks for another user and both users receive a
        notification without error.
    """

    fixtures = ['core-test-fixtures']

    @before
    def login(self):
        self.assertTrue(self.client.login(username='test1@example.com',
            password='1'))

    def test_posting_praise(self):
        """
            Tests that user is able to sucessfully praise another user
            that user is notified
        """

        resp = self.client.post(
            reverse('staff_directory:thanks', args=('admin', )), data={
                'value_type': 'serve', 'reason': 'because!',
                }, follow=True)

        recipient = Person.objects.filter(stub='admin')[0]
        self.assertTrue(Praise.objects.filter(recipient=recipient)\
            .filter(cfpb_value='serve').filter(reason='because!'))
        self.assertContains(resp, 'because!', status_code=200)
