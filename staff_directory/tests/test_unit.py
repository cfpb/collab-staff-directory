from django.test import TestCase

from collab.django_factories import UserF
from core.taggit.utils import add_tags
from core.models import Person
from core.taggit.models import TagCategory
from staff_directory.helpers import _get_emails_for_tag


class HelperTest(TestCase):

    def test_create_tags_for_person(self):
        user = UserF(username="jack@example.org")
        person = Person(user=user)
        person.save()

        tag_category = TagCategory(name='Test Category',
                                   slug='staff-directory-test-category')
        tag_category.save()

        tagged_item = add_tags(person, 'TagA',
                                'staff-directory-test-category', user, 'person')

        self.assertEqual(1, person.tags.count())


class TagEmailExportTest(TestCase):

    def test_single_tag_single_user(self):
        user = UserF(username="jack@example.org")
        person = Person(user=user)
        person.save()

        tag_category = TagCategory(name='Test Category',
                                   slug='staff-directory-test-category')
        tag_category.save()

        tags = []
        tagged_item = add_tags(person, 'TagA',
                                'staff-directory-test-category', user, 'person')
        tags.append(tagged_item.tag.slug)

        emails = _get_emails_for_tag(tags)
        self.assertTrue(len(emails) == 1)
        self.assertIn(user.email, emails)

    def test_single_tag_user_profile(self):
        user = UserF(username="jack@example.org")
        user.set_password("x")
        user.save()
        person = Person(user=user)
        person.stub = "jack"
        person.save()
        resp1 = self.client.login(username="jack@example.org", password="x")
        self.assertTrue(resp1)

        tag_category = TagCategory(name='Test Category',
                                   slug='staff-directory-test-category')
        tag_category.save()

        resp2 = self.client.post('/staff/add-person-to-tag/%s/hello!/' %
                                (person.stub), {'person_stub': person.stub,
                                                'tag_category': 'staff-directory-test-category'})

        self.assertContains(resp2, "redirect", status_code=200)

    def test_multiple_tags_single_user(self):
        user = UserF(username="jack@example.org")
        person = Person(user=user)
        person.save()

        tag_category = TagCategory(name='Test Category',
                                   slug='staff-directory-test-category')
        tag_category.save()

        tags = []
        tagged_item = add_tags(person, 'TagA',
                                'staff-directory-test-category', user, 'person')
        tags.append(tagged_item.tag.slug)
        tagged_item = add_tags(person, 'TagB',
                                'staff-directory-test-category', user, 'person')
        tags.append(tagged_item.tag.slug)

        emails = _get_emails_for_tag(tags)
        self.assertTrue(len(emails) == 1)
        self.assertIn(user.email, emails)

    def test_single_tag_multiple_users(self):
        user1 = UserF(username="jack@example.org")
        person1 = Person(user=user1)
        person1.save()

        user2 = UserF(username="jill@example.org")
        person2 = Person(user=user2)
        person2.save()

        tag_category = TagCategory(name='Test Category',
                                   slug='staff-directory-test-category')
        tag_category.save()

        tags = []
        tagged_item = add_tags(person1, 'TagA',
                                'staff-directory-test-category', user1, 'person')
        tagged_item = add_tags(person2, 'TagA',
                                'staff-directory-test-category', user1, 'person')
        tags.append(tagged_item.tag.slug)

        emails = _get_emails_for_tag(tags)
        self.assertTrue(len(emails) == 2)
        self.assertIn(user1.email, emails)
        self.assertIn(user2.email, emails)

    def test_multiple_tags_multiple_users(self):
        user1 = UserF(username="jack@example.org")
        person1 = Person(user=user1)
        person1.save()

        user2 = UserF(username="jill@example.org")
        person2 = Person(user=user2)
        person2.save()

        user3 = UserF(username="janice@example.org")
        person3 = Person(user=user3)
        person3.save()

        tag_category = TagCategory(name='Test Category',
                                   slug='staff-directory-test-category')
        tag_category.save()

        tags = []
        tagged_item = add_tags(person1, 'TagA',
                                'staff-directory-test-category', user1, 'person')
        tagged_item = add_tags(person2, 'TagA',
                                'staff-directory-test-category', user1, 'person')
        tags.append(tagged_item.tag.slug)

        tagged_item = add_tags(person2, 'TagB',
                                'staff-directory-test-category', user1, 'person')
        tagged_item = add_tags(person3, 'TagB',
                                'staff-directory-test-category', user2, 'person')
        tags.append(tagged_item.tag.slug)

        emails = _get_emails_for_tag(tags)
        self.assertTrue(len(emails) == 1)
        self.assertIn(user2.email, emails)

    def test_no_emails(self):
        user1 = UserF(username="jack@example.org")
        person1 = Person(user=user1)
        person1.save()

        user2 = UserF(username="jill@example.org")
        person2 = Person(user=user2)
        person2.save()

        tag_category = TagCategory(name='Test Category',
                                   slug='staff-directory-test-category')
        tag_category.save()

        tags = []
        tagged_item = add_tags(person1, 'TagA',
                                'staff-directory-test-category', user1, 'person')
        tags.append(tagged_item.tag.slug)

        tagged_item = add_tags(person2, 'TagB',
                                'staff-directory-test-category', user1, 'person')
        tags.append(tagged_item.tag.slug)

        emails = _get_emails_for_tag(tags)
        self.assertEqual(len(emails), 0)
