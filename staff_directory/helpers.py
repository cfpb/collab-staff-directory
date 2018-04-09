from django.db.models import Count

from core.models import Person
from core.taggit.models import Tag

STAFF_DIR_TAG_CATEGORIES = ['staff-directory-my-expertise',
                            'staff-directory-my-projects',
                            'staff-directory-other-things']

def _apply_profile_filters(queryset):
    return queryset.filter(user__is_active=True) \
    .filter(hide_profile=False) \
    .order_by('user__last_name', 'user__first_name') \
    .select_related('user')

def _set_remove_tag_permission(req, person, tags):
    user = person.user
    for tag in tags:
        for taggeditem in tag.taggit_taggeditem_items.all():
            tag.can_remove = user.id == req.user.id or \
                req.user == taggeditem.tag_creator
    return tags


def _set_taggers(req, person, tags, slug):
    for tag in tags:
        tag.taggers = ", ".join([user.person.full_name for user in
                                 tag.taggers(slug, person.id, 'person')])
    return tags


def _query_profile_tags(req, slug, profile_id):
    return Tag.objects.filter(
        taggit_taggeditem_items__tag_category__slug=slug,
        taggit_taggeditem_items__object_id=profile_id,
        taggit_taggeditem_items__content_type__name='person').annotate(
            tag_count=Count('taggit_taggeditem_items')) \
        .order_by('-tag_count', 'name')


def _query_tags_for_people(people):
    tags = dict()
    for category in STAFF_DIR_TAG_CATEGORIES:
        tags[category] = Tag.objects.filter(
            person__in=people,
            person__user__is_active=True,
            taggit_taggeditem_items__tag_category__slug=category) \
            .annotate(tag_count=Count('taggit_taggeditem_items')) \
            .order_by('-tag_count', 'name')
    return tags


def _get_emails_for_tag(tags):
    emails = []

    if len(tags) == 0:
        return emails

    selected_tag_pks = Tag.objects.filter(
        slug__in=tags).values_list('pk', flat=True)
    if selected_tag_pks.count() == 0:
        return emails

    people = Person.objects.filter(user__is_active=True) \
        .order_by('user__last_name')
    for pk in selected_tag_pks:
        people = people.filter(tags__pk=pk).distinct()

    emails = people.values_list('user__email', flat=True)
    return emails


def _get_emails_for_people(people):
    pass
