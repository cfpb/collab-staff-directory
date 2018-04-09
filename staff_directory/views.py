from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.db.models import Count, Q
from django.http import (
    Http404, HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect
)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.context_processors import csrf
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.views.decorators.cache import never_cache
from urllib import urlencode

from cache_tools.tools import expire_cache_group

from core.utils import json_response
from core.taggit.utils import add_tags
from core.helpers import user_has_profile
from core.models import Person, OrgGroup
from core.notifications.models import Notification
from core.notifications.email import EmailInfo
from core.taggit.models import Tag, TaggedItem
from staff_directory.helpers import _apply_profile_filters, \
    _get_emails_for_tag, _query_profile_tags, _query_tags_for_people, \
    _set_remove_tag_permission, _set_taggers, STAFF_DIR_TAG_CATEGORIES

from decorators import registration_required, user_allows_tagging
from models import Praise



TEMPLATE_PATH = 'staff_directory/'


def _create_params(req):
    p = {}
    p['is_staff_directory'] = True
    if settings.WIKI_INSTALLED:
        p['wiki_installed'] = True
        p['wiki_search_autocomplete_json_url'] = \
            settings.WIKI_SEARCH_URL % ('5', '')
    p.update(csrf(req))
    return p


def _add_person_data(req, p, person):
    p['person'] = person
    p['what_i_do_tags'] = _query_profile_what_i_do_tags(req, person)
    p['current_projects_tags'] = \
        _query_profile_current_projects_tags(req, person)
    p['other_tags'] = _query_profile_other_tags(req, person)
    p['thanks'] = Praise.objects.filter(recipient=person). \
        order_by('-date_added'). \
        select_related('praise_nominator',
                       'praise_nominator__person')


def _query_profile_what_i_do_tags(req, person):
    tags = _query_profile_tags(req, 'staff-directory-my-expertise',
                               person.id)
    tags = _set_remove_tag_permission(req, person, tags)
    tags = _set_taggers(req, person, tags, 'staff-directory-my-expertise')

    return tags


def _query_profile_current_projects_tags(req, person):
    tags = _query_profile_tags(req, 'staff-directory-my-projects',
                               person.id)
    tags = _set_remove_tag_permission(req, person, tags)
    tags = _set_taggers(req, person, tags, 'staff-directory-my-projects')

    return tags


def _query_profile_other_tags(req, person):
    tags = _query_profile_tags(req, 'staff-directory-other-things',
                               person.id)
    tags = _set_remove_tag_permission(req, person, tags)
    tags = _set_taggers(req, person, tags, 'staff-directory-other-things')
    return tags


@login_required
@registration_required
@cache_page(60 * 2)
def index(req, format='html'):
    """
    index of fedmash, display photos of new staff, teams and popular tags
    """
    if not user_has_profile(req.user):
        return HttpResponseRedirect(reverse('core:register'))
    p = _create_params(req)
    people = _apply_profile_filters(Person.objects)
    p['recent_photos'] = people.filter(
        ~Q(photo_file="avatars/default.jpg")).order_by('-updated_at')[:20]
    p['divisions'] = OrgGroup.objects.filter(parent=None).order_by('title')
    p['offices'] = OrgGroup.objects.exclude(parent=None).order_by(
        'parent__title', 'title')
    p['tags'] = Tag.objects.filter(
        person__user__is_active=True,
        taggit_taggeditem_items__content_type__name='person'). \
        annotate(tag_count=Count('taggit_taggeditem_items')). \
        filter(tag_count__gte=20).order_by('-tag_count', 'name')
    return render_to_response(TEMPLATE_PATH + 'directory.html', p,
                              context_instance=RequestContext(req))


@login_required
@never_cache
def person_profile(req, stub):
    """
        display user's profile page
    """

    user = get_object_or_404(get_user_model(), person__stub=stub)

    p = _create_params(req)

    person = user.get_profile()

    if not user.is_active or person.hide_profile:
        raise Http404

    person.format_phone_numbers()

    _add_person_data(req, p, person)

    p['tagging_allowed'] = (person.allow_tagging) or (user == req.user)
    p['draft_thanks'] = req.GET.get('draft_thanks') or None

    return render_to_response(
        TEMPLATE_PATH + 'profile.html',
        p,
        context_instance=RequestContext(req)
    )


@csrf_protect
@login_required
def add_person_to_tag(req, tag=''):
    if req.method == 'POST':
        person_stub = req.POST.get('person_stub', '').strip()
        tag_category = req.POST.get('tag_category',
                                    'staff-directory-other-things').strip()
        expire_cache_group('tags')
        return add_tag(req, person_stub, tag,
                       tag_category, True, True)


@csrf_protect
@login_required
@user_allows_tagging
def add_tag(req, person_stub='', tag='', category_slug='', is_ajax=False,
            redirect_to_tags_page=False):
    """
        adds a tag to a user if they do not have tagging turned off
    """
    if req.method == 'POST':
        if tag == '':
            tag = req.POST.get('tag', '').strip()
        if category_slug == '':
            category_slug = req.POST.get('tag_category_slug', '').strip()
        if tag == '':
            return json_response({'error':
                                 'Please enter a tag that is not blank.'})
        elif person_stub == '':
            return json_response({'error':
                                 'Person not found.'})
        person = Person.objects.get(stub=person_stub)
        # make sure tag does not already exist
        try:
            taggeditem = TaggedItem.objects.get(
                tag_category__slug=category_slug, object_id=person.id,
                tag__name__iexact=tag)
        except Exception:
            taggeditem = add_tags(person, tag, category_slug, req.user,
                                  'person')
            person.expire_cache()
            expire_cache_group('tags')

        url = reverse('staff_directory:person', args=[person.stub])
        if person.user != req.user:
            email_info = EmailInfo(
                subject='You were tagged in the staff directory!',
                text_template='staff_directory/email/user_tagged.txt',
                html_template='staff_directory/email/user_tagged.html',
                to_address=person.user.email,
            )
            # set notification
            title = '%s %s tagged you with "%s"' % \
                (req.user.first_name, req.user.last_name, tag)
            Notification.set_notification(req.user, req.user, "tagged", tag,
                                          person.user, title, url, email_info)
        if is_ajax:
            if redirect_to_tags_page:
                return json_response({'redirect':
                                       reverse('staff_directory:show_by_tag',
                                               args=[taggeditem.tag.slug])})
            return json_response({'redirect':
                                   reverse('staff_directory:person', args=[person.stub])})
        else:
            return HttpResponseRedirect(reverse('staff_directory:person',
                                                args=[person.stub]))


@login_required
def remove_tag(req, person_stub, tag_slug, tag_category):
    """
        web service to remove tag from profile, users are only able to
        remove their own tags
    """
    person = Person.objects.get(stub=person_stub)
    tag = Tag.objects.get(slug=tag_slug)
    taggeditem = TaggedItem.objects.get(tag_category__slug=tag_category,
                                        object_id=person.id, tag=tag)
    taggeditem.delete()
    person.expire_cache()
    expire_cache_group('tags')

    url = reverse('staff_directory:person', args=[person.stub])

    if person.user != req.user:
        # create email info
        email_info = EmailInfo(
            subject='A tag was removed from your user profile.',
            text_template='staff_directory/email/user_untagged.txt',
            html_template='staff_directory/email/user_untagged.html',
            to_address=person.user.email,
        )

        # set notification
        title = '%s %s removed the "%s" tag from your profile' % \
            (req.user.first_name, req.user.last_name, tag)
        Notification.set_notification(req.user, req.user, "untagged", tag,
                                      person.user, title, url, email_info)
    return HttpResponseRedirect(url)


@login_required
@registration_required
def org_group(req, title, tag_slugs=''):
    """
        team page, display users in a team
        if org group is a department, show users from all teams in
        department. if not, org group = team, just display members of team
    """
    p = _create_params(req)
    p['title'] = title

    org_groups = OrgGroup.objects.filter(title=title).select_related()

    if len(org_groups) == 0:
        raise Http404

    org_group = org_groups[0]
    if not org_group.parent:
        people = _apply_profile_filters(Person.objects)
        people = people.filter(Q(org_group=org_group) |
                    Q(org_group__parent=org_group))
    else:
        people = _apply_profile_filters(org_group.person_set)

    if tag_slugs != '':
        tag_slugs_list = [t for t in tag_slugs.split('/')]
        selected_tags = Tag.objects.filter(slug__in=tag_slugs_list)
        selected_tag_pks = [t.pk for t in selected_tags]
        p['selected_tags'] = '/'.join([t.slug for t in selected_tags])

        people = people.filter(tags__pk__in=selected_tag_pks).distinct()

        p['title'] = title + " tagged with: " + ', '.join(
            [t.name for t in selected_tags])

    p['tags'] = _query_tags_for_people(people)
    p['tag_category_names'] = {
        'staff-directory-my-projects': 'Projects',
        'staff-directory-my-expertise': 'Expertise',
        'staff-directory-other-things': 'Other Things',
    }
    p['people'] = people
    p['org_group'] = org_group

    if req.GET.get('format', '') == 'csv':
        emails = people.values_list('user__email', flat=True)
        emails_text = '; '.join(emails)
        return HttpResponse(emails_text)
    else:
        return render_to_response(TEMPLATE_PATH + 'display_group.html', p,
                                  context_instance=RequestContext(req))


@login_required
@csrf_protect
def thanks(req, stub):
    if req.method == 'POST':
        praise = Praise()
        praise.recipient = get_object_or_404(Person, stub=stub)
        praise.praise_nominator = req.user
        praise.cfpb_value = req.POST.get('value_type', '').lower()
        praise.reason = req.POST.get('reason', '')
        if praise.recipient.user != praise.praise_nominator:
            praise.save()
        return HttpResponseRedirect(reverse('staff_directory:person', args=[stub]))
    else:
        raise Http404


@login_required
def show_thanks(req):
    p = _create_params(req)
    thanks_list = Praise.objects.all().order_by('-date_added'). \
        select_related('praise_nominator', 'recipient',
                       'praise_nominator__person', 'recipient__user')
    items_per_page = getattr(settings, 'STAFF_THANKS_PAGINATION_LIMIT', 10)
    paginator = Paginator(thanks_list, items_per_page)
    page_num = req.GET.get('page_num')

    # Parse the page number, if any.  Copied from this guide:
    # https://docs.djangoproject.com/en/1.6/topics/pagination/
    try:
        page = paginator.page(page_num)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        page = paginator.page(paginator.num_pages)

    total_pages = page.paginator.num_pages
    mypage = page.number
    bottom_limit = 15
    # flex_range is an array of 15 (or less) numbers centered around the
    # current page.  For example, if there are 100 pages and the current
    # page is 35, the range will be [28 ... 42]
    if mypage <= bottom_limit/2:
        flex_range = range(1, min(bottom_limit, total_pages)+1)
    elif mypage > (total_pages - bottom_limit/2):
        flex_range = range(total_pages-bottom_limit, total_pages+1)
    else:
        flex_range = range(mypage - bottom_limit/2, mypage + bottom_limit/2 + 1)

    p['thanks_list'] = page
    p['flex_page_range'] = flex_range
    return render_to_response('staff_directory/show_thanks.html', p,
                              context_instance=RequestContext(req))


@login_required
@never_cache
#define show by tag with 3 parameters, req, tag_slugs, and new_tag_slug
def show_by_tag(req, tag_slugs='', new_tag_slug=''):

    if req.method == 'GET':
        p = _create_params(req)

        tag_slugs_list = [t for t in tag_slugs.split('/')]

        if len(tag_slugs_list) == 0:
            return HttpResponseRedirect(reverse('staff_directory:index'))

        selected_tags = Tag.objects.filter(slug__in=tag_slugs_list)

        if selected_tags.count() == 0:
            return HttpResponseRedirect(reverse('staff_directory:index'))
        # if only a single tag, show 'add tag to person' block
        if selected_tags.count() == 1:
            p['single_tag'] = selected_tags[0]

        selected_tag_pks = Tag.objects.filter(
            slug__in=tag_slugs_list).values_list('pk', flat=True)

        people = _apply_profile_filters(Person.objects)

        for pk in selected_tag_pks:
            people = people.filter(tags__pk=pk).distinct()

        tags = Tag.objects.filter(
            person__in=people,
            person__user__is_active=True,
            taggit_taggeditem_items__tag_category__slug__in=
            STAFF_DIR_TAG_CATEGORIES).annotate(
                tag_count=Count('taggit_taggeditem_items'),
            ). \
            order_by('-tag_count', 'slug')

        title_tags = ','.join(t.name for t in selected_tags)

        # Create a list of selected tags to compare new selections
        selected_tags_list = []
        for t in selected_tags:
            selected_tags_list.append(t.slug)

        selected_tags_list.sort()

        # this array is to limit returns of non-selected tags
        passed_tags = []
        for t in tags:
            if t.slug in selected_tags_list:
                #do nothing
                pass
            elif len(passed_tags) < 30:
                passed_tags.append(t)

        p['title'] = "Tagged with %s" % title_tags
        p['people'] = people
        p['tags'] = tags
        p['selected_tags'] = tag_slugs
        p['passed_tags'] = passed_tags

        # Pass a list to the page so we can compare whether selected tag already exists
        p['selected_tags_list'] = selected_tags_list

        # TODO: should show page that no one is tagged with that tag
        return render_to_response(TEMPLATE_PATH + 'display_group.html', p,
                                  context_instance=RequestContext(req))

@login_required
def show_tag_emails(req, tag_slugs=''):
    tag_slugs_list = []
    for t in tag_slugs.split('/'):
        if not t.strip() == '':
            tag_slugs_list.append(t)

    emails = _get_emails_for_tag(tag_slugs_list)

    if len(emails) == 0:
        return HttpResponse("There are no active users with this tag.")

    emails_text = '; '.join(emails)
    return HttpResponse(emails_text)


@login_required
@never_cache
def lookup(req):
    if req.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    email = req.GET.get('email') or ''

    try:
        person = Person.objects.get(user__email__iexact=email)
    except Person.DoesNotExist:
        raise Http404

    url = reverse('staff_directory:person', args=(person.stub,))

    params = dict(req.GET.items())
    params.pop('email')

    return HttpResponseRedirect(url + '?' + urlencode(params))
