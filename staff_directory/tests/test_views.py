from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.html import escape

from core.taggit.utils import add_tags
from core.taggit.models import TagCategory
from core.models import Person, OrgGroup
from exam.cases import Exam
from exam.decorators import before
from core.notifications.email import EmailInfo
from core.notifications.models import Notification
from staff_directory.models import Praise


class TagPageTests(Exam, TestCase):
    fixtures = ['sd-test-fixtures.json', ]

    @before
    def login(self):
        self.assertTrue(self.client.login(username='test1@example.com', password='1'))

    def test_staff_page(self):
        """
            Tests the home staff directory page appears with no errors.
        """
        selected_tags = "22/25/30"
        resp = self.client.get(reverse('staff_directory:show_by_tag" tag_slugs=selected_tags'))
        self.assertContains(resp, 'Tagged with', status_code=200)

class SmokeTests(Exam, TestCase):
    fixtures = ['sd-test-fixtures.json', ]

    @before
    def login(self):
        self.assertTrue(self.client.login(username='test1@example.com', password='1'))

    def test_staff_page(self):
        """
            Tests the home staff directory page appears with no errors.
        """
        resp = self.client.get(reverse('staff_directory:index'))
        self.assertContains(resp, 'Staff Directory', status_code=200)

    def test_profile_page(self):
        """
            Tests the profile page appears with no errors.
        """
        person = Person.objects.all()[1]
        resp = self.client.get(reverse('staff_directory:person', args=(person.stub,)))
        self.assertContains(resp, person.full_name, status_code=200)

    def test_profile_page_non_existent_user(self):
        """
            Tests the 404 is risen when querying a non user.
        """
        resp = self.client.get(reverse('staff_directory:person', args=('not-really-a-user',)))
        self.assertEqual(resp.status_code, 404)

    def test_profile_page_of_inactive_user(self):
        """
            Tests the profile page of an inactive user.
        """
        person = Person.objects.all()[1]

        user = person.user
        user.is_active = False
        user.save()

        resp = self.client.get(reverse('staff_directory:person', args=(person.stub,)))

        self.assertEqual(resp.status_code, 404)


class TaggingTests(Exam, TestCase):
    fixtures = ['sd-test-fixtures.json', ]

    @before
    def login(self):
        self.assertTrue(self.client.login(username='test1@example.com', password='1'))

    def test_profile_page_with_removed_tagger(self):
        """
            Tests the profile page appears with no errors.
        """
        person = Person.objects.all()[1]

        user = User(first_name="Baba", last_name="O'Reilly")
        user.save()

        tag_category = TagCategory(name='Test Category',
                                   slug='staff-directory-test-category')
        tag_category.save()

        add_tags(person, 'TagA',
                  'staff-directory-test-category', user, 'person')

        resp = self.client.get(reverse('staff_directory:person', args=(person.stub,)))
        self.assertContains(resp, person.full_name, status_code=200)


class OrgGroupTest(Exam, TestCase):
    fixtures = ['sd-test-fixtures.json', ]

    @before
    def login(self):
        self.assertTrue(self.client.login(username='test1@example.com', password='1'))

    def test_org_group_page(self):
        """
            Tests the org group page appears with no errors.
        """
        org = OrgGroup.objects.all()[0]
        resp = self.client.get(reverse('staff_directory:org_group', args=(org.title, )))

        self.assertContains(resp, escape(org.title), status_code=200)

    def test_org_group_page_with_tags(self):
        """
            Tests the org group filters by tag.
        """
        org = OrgGroup.objects.filter(pk=51)[0]
        person_tagged = org.person_set.all()[0]
        person_not_tagged = org.person_set.all()[1]

        add_tags(person_tagged, 'TagA',
                  'staff-directory-my-expertise', person_tagged.user, 'person')

        resp = self.client.get(reverse(
            'staff_directory:org_group_with_tags', args=(org.title, 'taga')))
        self.assertContains(resp, escape(
            person_tagged.full_name), status_code=200)
        self.assertNotContains(resp, escape(
            person_not_tagged.full_name), status_code=200)
