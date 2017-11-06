import datetime # use this only for checking types. use django.utils.datetime_safe for handling actual dates

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import models, transaction
from django.db.models import permalink, Q
from django.db.models.query import EmptyQuerySet
from django.utils.datetime_safe import date
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType

from model_utils import Choices
from model_utils.managers import PassThroughManager
from model_utils.models import TimeStampedModel

from sorl.thumbnail import ImageField

from open_municipio.monitoring.models import MonitorizedItem
from open_municipio.newscache.models import NewsTargetMixin
from open_municipio.people.managers import ( TimeFramedQuerySet, GroupQuerySet,
                                        ChargeQuerySet )
from open_municipio.om_utils.models import SlugModel

import open_municipio

from collections import Counter

#
# Persons, charges and groups
#

class Person(models.Model, MonitorizedItem):
    """
        The ``related_news`` attribute can be used  to fetch news related to a given person.
    """
    FEMALE_SEX = 0
    MALE_SEX = 1
    SEX = Choices(
        (MALE_SEX, _('Male')),    
        (FEMALE_SEX, _('Female')),
        )
    first_name = models.CharField(_('first name'), max_length=128)
    last_name = models.CharField(_('last name'), db_index=True, max_length=128)
    birth_date = models.DateField(_('birth date'))
    birth_location = models.CharField(_('birth location'), blank=True, max_length=128)
    slug = models.SlugField(unique=True, blank=True, null=True, max_length=128)
    sex = models.IntegerField(_('sex'), choices=SEX)
    op_politician_id = models.IntegerField(_('openpolis politician ID'), blank=True, null=True)

    img = ImageField(upload_to="person_images", blank=True, null=True)

    # manager to handle the list of monitoring having as content_object this instance
    #monitoring_set = generic.GenericRelation(Monitoring, object_id_field='object_pk')
    
    class Meta:
        verbose_name = _('person')
        verbose_name_plural = _('people')
   
    def __unicode__(self):
        return u'%s, %s' % (self.last_name, self.first_name)

    def save(self, *args, **kwargs):
        if self.slug is None:
            self.slug = slugify("%s %s %s" % (self.first_name, self.last_name, self.birth_date))
        super(Person, self).save(*args, **kwargs)

    @permalink
    def get_absolute_url(self):
        return 'om_politician_detail', (), { 'slug': self.slug }

    @property
    def openpolis_link(self):
        link = None

        if self.op_politician_id:
            link = settings.OP_URL_TEMPLATE % { "op_id":self.op_politician_id }
    
        return link            

    @property
    def is_om_user(self):
        """
        check whether the person is a registered om user
        """
        try:
            prof = self.userprofile
            return True
        except ObjectDoesNotExist:
            return False

    @property
    def full_name(self):
        return "%s %s" % (self.first_name, self.last_name)
   
    @property
    def all_institution_charges(self):
        """
        Returns the QuerySet of all institution charges held by this person during his/her career.
        """
        return self.institutioncharge_set.select_related().all()


    def get_past_institution_charges(self, moment=None):
        return self.institutioncharge_set.select_related().past(moment=moment)\
            .exclude(institution__institution_type__in=(Institution.COMMITTEE, Institution.JOINT_COMMITTEE))\
            .order_by('-start_date')

    past_institution_charges = property(get_past_institution_charges)

    def get_current_institution_charges(self, moment=None):
        """
        Returns the current institution charges at the given moment (no committees).
        """
        return self.institutioncharge_set.select_related().current(moment=moment).exclude(
            institution__institution_type__in=(Institution.COMMITTEE, Institution.JOINT_COMMITTEE)
        )
    current_institution_charges = property(get_current_institution_charges)

    def get_current_committee_charges(self, moment=None):
        """
        Returns the current committee charges, at the given moment.
        """
        return self.institutioncharge_set.select_related().current(moment=moment).filter(
            institution__institution_type__in=(Institution.COMMITTEE, Institution.JOINT_COMMITTEE)
        ).order_by('-institutionresponsability__charge_type','institution__position')
    current_committee_charges = property(get_current_committee_charges)


    def get_current_charge_in_institution(self, institution, moment=None):
        """
        Returns the current charge in the given institution at the given moment.
        Returns empty array if no charges are found.
        """
        charges = self.institutioncharge_set.select_related().current(moment=moment).filter(
            institution=institution
        )

        curr_charge = None
        try:
            curr_charge = charges[0]
        except IndexError:
            raise ObjectDoesNotExist

    def has_current_charges(self, moment=None):
        """
        Used for admin interface
        """
        if self.institutioncharge_set.current(moment).count() > 0:
            return True
        else:
            return False
    has_current_charges.short_description = _('Current')

    def is_counselor(self, moment=None):
        """
        check if the person is a member of the council at the given moment
        """
        if self.current_counselor_charge(moment):
            return True
        else:
            return False

    def current_counselor_charge(self, moment=None):
        """
        fetch the current charge in Council, if any
        """
#        i = Institution.objects.get(institution_type=Institution.COUNCIL)
        i = CityCouncil().as_institution
        try:
            ic = self.get_current_charge_in_institution(i, moment)
            return ic
        except ObjectDoesNotExist:
            return None

    def last_charge(self, moment=None):
        """
        last charge, if any
        """
        charges = self.current_institution_charges if self.has_current_charges() else self.past_institution_charges
        try:
            return charges[0]
        except IndexError:
            raise ObjectDoesNotExist


    def get_historical_groupcharges(self, moment=None):
        """
        Returns all groupcharges for the person
        """
#        i = Institution.objects.get(institution_type=Institution.COUNCIL)  
        i = CityCouncil().as_institution
        try:
            ic = self.get_current_charge_in_institution(i, moment)
            gc = GroupCharge.objects.select_related().past(moment).filter(charge=ic)
        except ObjectDoesNotExist:
            gc = None
        return gc
    historical_groupcharges = property(get_historical_groupcharges)


    def get_current_groupcharge(self, moment=None):
        """
        Returns GroupCharge at given moment in time (now if moment is None)
        Charge is the IntstitutionalCharge in the council
        """
#        i = Institution.objects.get(institution_type=Institution.COUNCIL)
        i = CityCouncil().as_institution
        try:
            ic = self.get_current_charge_in_institution(i, moment)
            gc = GroupCharge.objects.select_related().current(moment).get(charge=ic)
        except ObjectDoesNotExist:
            gc = None
        return gc
    current_groupcharge = property(get_current_groupcharge)

    def get_current_group(self, moment=None):
        """
        Returns group at given moment in time (now if moment is None)
        Group is computed from GroupCharge where Charge is the IntstitutionalCharge in the council
        Returns None if there is no current group.
        """
        group = None
        try:
            group = self.get_current_groupcharge(moment).group
        except AttributeError:
            pass
#        if gc is None:
#            return None
#        return gc.group

        return group
    current_group = property(get_current_group)


    @property
    def resources(self):
        """
        Returns the list of resources associated with this person
        """
        return self.resource_set.all()
    
    @property
    def content_type_id(self):
        """
        Return id of the content type associated with this instance.
        """
        return ContentType.objects.get_for_model(self).id

    @property
    def age(self):
        """
        Returns an integer of year between birth_date and now
        """
        #end_date = in_date if in_date else date.today()
        return (date.today() - self.birth_date).days / 365

    @property
    def related_news(self):
        """
        News related to a politician are the union of the news related to allthe politician's
        current and past institution charges
        """
        news = EmptyQuerySet()
        for c in self.all_institution_charges:
            news |= c.related_news
        return news

    @property
    def speeches(self):
        """
        Speeches of a politician
        """
        from open_municipio.acts.models import Speech

        return Speech.objects.filter(author=self)

    @property
    def n_speeches(self):
        """
        Number of speeches of a politician
        """
        return self.speeches.count()

    @property
    def speeches_size(self):
        """
        Number of speeches of a politician
        """
        return sum([s.text_size for s in self.speeches.all()])


class Resource(models.Model):
    """
    This class maps the internet resources (mail, web sites, rss, facebook, twitter, )
    It must be subclassed, by a PersonResource, InstitutionResource or GroupResource class.

    The `value` field contains the resource.
    The `description` field may be used to specify the context.

    A `PERSON` resource may be a secretary, a responsible. We're interested only in
    her name, it must not be mapped into the system.
    """
    RES_TYPE = Choices(
        ('EMAIL', 'email', _('email')),
        ('URL', 'url', _('url')),
        ('PHONE', 'phone', _('phone')),
        ('FAX', 'fax', _('fax')),
        ('SNAIL', 'snail', _('snail mail')),
        ('PERSON', 'person', _('person')),
        ('TWITTER', 'twitter', _('twitter')),
        ('FACEBOOK', 'facebook', _('facebook')),
        ('FINANCIAL', 'financial', _('financial information')),
    )
    resource_type = models.CharField(verbose_name=_('type'), max_length=10, choices=RES_TYPE)
    # 2000 chars is the maximum length suggested for url length (see: http://stackoverflow.com/questions/417142/what-is-the-maximum-length-of-a-url-in-different-browsers )
    value = models.CharField(verbose_name=_('value'), max_length=2000)
    description = models.CharField(verbose_name=_('description'), max_length=255, blank=True)

    class Meta:
        abstract = True
        verbose_name = _('Resource')
        verbose_name_plural = ('Resources')

class PersonResource(Resource):
    person = models.ForeignKey('Person', verbose_name=_('person'), related_name='resource_set')

class InstitutionResource(Resource):
    institution = models.ForeignKey('Institution', verbose_name=_('institution'), related_name='resource_set')

class GroupResource(Resource):
    group = models.ForeignKey('Group', verbose_name=_('group'), related_name='resource_set')


class Charge(NewsTargetMixin, models.Model):
    """
    This is the base class for the different macro-types of charges (institution, organization, administration).

    The ``related_news`` attribute can be used  to fetch news items related to a given charge.
    """
    person = models.ForeignKey('Person', verbose_name=_('person'))
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'), blank=True, null=True)
    end_reason = models.CharField(_('end reason'), blank=True, max_length=255)
    description = models.CharField(_('description'), blank=True, max_length=255,
                                   help_text=_('Insert the complete description of the charge, if it gives more information than the charge type'))
    
#    objects = PassThroughManager.for_queryset_class(TimeFramedQuerySet)()
    objects = PassThroughManager.for_queryset_class(ChargeQuerySet)()


    class Meta:
        abstract = True

    def get_absolute_url(self):
        return self.person.get_absolute_url()

#    @property
    def is_in_charge(self, as_of=None):
        
        if not as_of:
            #as_of = datetime.now()
            as_of = date.today()

        # if a datetime, extract the date part
        if isinstance(as_of, datetime.datetime):
            as_of = as_of.date()
        
        # check we receive a date (note: a datetime is also a date, but
        # we already took care of this case in the previous lines)
        if not isinstance(as_of, datetime.date):
            raise ValueError("The passed parameter is not a date")
        
        return as_of >= self.start_date and (not self.end_date or as_of <= self.end_date)

    @property
    def duration(self):

        if not self.start_date: return None

#        return (self.end_date if self.end_date else datetime.datetime.now().date()) - self.start_date
        return (self.end_date if self.end_date else date.today()) - self.start_date

    @property
    def speeches(self):
        """
        Speeches of a charge
        """
        start_date = self.start_date;
        end_date = self.end_date if self.end_date else datetime.datetime.now();

        return open_municipio.acts.models.Speech.objects.filter(\
            author=self.person, sitting_item__sitting__date__range=(start_date, end_date))

    @property
    def n_speeches(self):
        """
        Number of speeches of a charge
        """
        return self.speeches.count()

    @property
    def speeches_size(self):
        """
        Number of speeches of a charge
        """
        return sum([s.text_size for s in self.speeches.all()])


class ChargeResponsability(models.Model):
    """
    Describes a responsability that the  charge has
    inside the charge's *container*. It integrates the composition relation.

    For example: a counselor may be the president of the council.

    This is an abstract class, that must be subclassed, in order to specify
    the context (institution charge or group charge)
    """
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'), blank=True, null=True)
    description = models.CharField(_('description'), blank=True, max_length=255,
                                   help_text=_('Insert an extended description of the responsability'))

    objects = PassThroughManager.for_queryset_class(TimeFramedQuerySet)()

    class Meta:
        abstract = True


class InstitutionCharge(Charge):
    """
    This is a charge in the institution (city council, city government, mayor, committee).
    """
    substitutes = models.OneToOneField('InstitutionCharge', blank=True, null=True,
                     related_name='reverse_substitute_set',
                     on_delete=models.PROTECT,
                     verbose_name=_('in substitution of'))
    substituted_by = models.OneToOneField('InstitutionCharge', blank=True, null=True,
                     related_name='reverse_substituted_by_set',
                     on_delete=models.PROTECT,
                     verbose_name=_('substituted by'))
    institution = models.ForeignKey('Institution', on_delete=models.PROTECT, verbose_name=_('institution'), related_name='charge_set')
    op_charge_id = models.IntegerField(_('openpolis institution charge ID'), blank=True, null=True)
    original_charge = models.ForeignKey('InstitutionCharge', blank=True, null=True,
                                           related_name='committee_charge_set',
                                           verbose_name=_('original institution charge'))
    n_rebel_votations = models.IntegerField(default=0, db_index=True)
    n_present_votations = models.IntegerField(default=0, db_index=True, verbose_name=_("number of presences during votes"))
    n_absent_votations = models.IntegerField(default=0, db_index=True, verbose_name=_("number of absences during votes"))
    n_present_attendances = models.IntegerField(default=0, db_index=True, verbose_name=_("number of present attendances"))
    n_absent_attendances = models.IntegerField(default=0, db_index=True, verbose_name=_("number of absent attendances"))

    can_vote = models.BooleanField(default=True, verbose_name=_("in case of a city council member, specifies whether he/she can vote"))

    def get_absolute_url(self):

        url = None

        if self.institution.institution_type == Institution.COMMITTEE:
            url = self.person.get_absolute_url()
        else:
            url = reverse("om_politician_detail", 
                kwargs={"slug":self.person.slug, 
                    "institution_slug": self.institution.slug,
                    "year":self.start_date.year, "month": self.start_date.month, 
                    "day":self.start_date.day })

        return url

    def is_counselor(self):
        return self.institution.institution_type == Institution.COUNCIL

    @property
    def is_in_city_government(self):
        return (self.institution.institution_type == Institution.CITY_GOVERNMENT or \
            self.institution.institution_type == Institution.MAYOR)


    class Meta(Charge.Meta):
        db_table = u'people_institution_charge'
        verbose_name = _('institution charge')
        verbose_name_plural = _('institution charges')
        ordering = ['person__first_name', 'person__last_name']


    def __unicode__(self):
        if self.denomination:
            return u"%s %s - %s" % (self.person.first_name, self.person.last_name, self.denomination)
        else:
            return u"%s %s" % (self.person.first_name, self.person.last_name)


    # TODO: model validation: check that ``substitutes`` and ``substituted_by`` fields
    # point to ``InstitutionCharge``s of the same kind

    @property
    def denomination(self):
        if self.institution.institution_type == Institution.MAYOR:
            denomination = _('Mayor') #.translate(settings.LANGUAGE_CODE) #-FS why?
            if self.description != "":
                denomination += ", %s" % self.description
            return denomination
        elif self.institution.institution_type == Institution.CITY_GOVERNMENT:

            try:
                responsibility = self.responsabilities[0]
                s = responsibility.get_charge_type_display()
                if responsibility.charge_type == InstitutionResponsability.CHARGE_TYPES.firstdeputymayor:
                    s += ", %s" % self.description
                return "%s" % (s, )
            except IndexError:
                return " %s" % self.description
        elif self.institution.institution_type == Institution.COUNCIL:
            try:
                return "%s Consiglio Comunale" % (self.responsabilities[0].get_charge_type_display(),)
            except IndexError:
                return _('Counselor')
        elif self.institution.institution_type == Institution.COMMITTEE:
            try:
                responsibility = self.responsabilities[0]
                return "%s" % (responsibility.get_charge_type_display())
            except IndexError:
                return _('Member').translate(settings.LANGUAGE_CODE)
        else:
            return ''

    @property
    def committee_charges(self):
        return self.committee_charge_set.all()

    @property
    def responsabilities(self):
        return self.institutionresponsability_set.all()

    def get_current_responsability(self, moment=None):
        """
        Returns the current group responsability, if any
        """
        responsibility = None
        try:
            responsibility = self.responsabilities.current(moment=moment)[0]
        except IndexError:  
            pass
    
        return responsibility
    current_responsability = property(get_current_responsability)


    @property
    def presented_acts(self):
        """
        The QuerySet of acts presented by this charge.
        """
        return self.presented_act_set.all()

    @property
    def n_presented_acts(self):
        """
        The number of acts presented by this charge
        """
        return self.presented_acts.count()

    @property
    def received_acts(self):
        """
        The QuerySet of acts received by this charge.
        """
        return self.received_act_set.all()

    @property
    def n_received_acts(self):
        """
        The QuerySet of acts received by this charge.
        """
        return self.received_act_set.count()

    @property
    def charge_type(self):
        """
        Returns the basic charge type translated string, according to the institution.

        For example: the council president's basic type is counselor.
        """
        if self.institution.institution_type == Institution.MAYOR:
            return _('Mayor')
        elif self.institution.institution_type == Institution.CITY_GOVERNMENT:
            return _('City government member')
        elif self.institution.institution_type == Institution.COUNCIL:
            return _('Counselor')
        elif self.institution.institution_type == Institution.COMMITTEE:
            return _('Committee member')
        else:
            return 'Unknown charge type!'

    @property
    def charge_type_verbose(self):
        """
        """
        s = self.charge_type

        if self.start_date:

            if self.end_date and self.start_date.year == self.end_date.year:
                s += ' nel ' + str(self.start_date.year)
            else:
                s += ' dal ' + str(self.start_date.year)

                if self.end_date:
                    s += ' al ' + str(self.end_date.year)

        return s

    @property
    def council_group(self):
        """
        DEPRECATED: use `self.current_groupcharge.group`

        Returns the city council's group this charge currently belongs to (if any).
        """
        return self.current_groupcharge.group

    @property
    def current_groupcharge(self):
        """
        Returns the current group related to a council charge (end_date is null).
        A single GroupCharge object is returned. The group may be accessed by the `.group` attribute

        A Council Institution charge MUST have one group.
        Other types of charge do not have a group, so None is returned.
        """
        return self.current_at_moment_groupcharge()

    def current_at_moment_groupcharge(self, moment=None):
        """
        Returns groupcharge at given moment in time.
        If moment is None, then current groupcharge is returned
        """
        if self.institution.institution_type == Institution.COUNCIL:
            try:
                return GroupCharge.objects.select_related().current(moment=moment).get(charge__id=self.id)
            except GroupCharge.DoesNotExist:
                return None

        elif self.original_charge and \
            (self.institution.institution_type == Institution.COMMITTEE or \
             self.institution.institution_type == Institution.JOINT_COMMITTEE):
            try:
                return GroupCharge.objects.select_related().current(moment=moment).get(charge=self.original_charge)
            except GroupCharge.DoesNotExist:
                return None

        else:
            return None

    @property
    def historical_groupcharges(self):
        """
        Returns the list of past groups related to a council charge (end_date is not null).
        A list of GroupCharge objects is returned. The group may be accessed by the `.group` attribute
        """
        if self.institution.institution_type == Institution.COUNCIL:
            return GroupCharge.objects.select_related().past().filter(charge__id=self.id)
        else:
            return []

    def update_rebellion_cache(self):
        """
        Re-compute the number of votations where the charge has vote differently from her group
        and update the n_rebel_votations counter
        """
        self.n_rebel_votations = self.chargevote_set.filter(is_rebel=True).count()
        self.save()

    def update_presence_cache(self):
        """
        Re-compute the number of votations where the charge was present/absent
        and update the respective counters
        """
        from open_municipio.votations.models import ChargeVote
        from open_municipio.attendances.models import ChargeAttendance
         
        absent = ChargeVote.VOTES.absent
        self.n_present_votations = self.chargevote_set.exclude(vote=absent).count()
        self.n_absent_votations = self.chargevote_set.filter(vote=absent).count()

        self.n_present_attendances = self.chargeattendance_set.filter(value=ChargeAttendance.VALUES.pres).count()
        self.n_absent_attendances = self.chargeattendance_set.exclude(value=ChargeAttendance.VALUES.pres).count()
        self.save()

    @property
    def taxonomy_count(self):

        count = { 'categories' : Counter(), 'tags' : Counter(), 'topics' : Counter(), 'locations' : Counter() }

        for act in self.presented_acts:
            count['categories'].update(act.categories)
            count['tags'].update(act.tags)
            count['locations'].update(act.locations)

        return count


class InstitutionResponsability(ChargeResponsability):
    """
    Responsability for institutional charges.
    """
    CHARGE_TYPES = Choices(
        ('MAYOR', 'mayor', _('Mayor')),
        ('FIRSTDEPUTYMAYOR', 'firstdeputymayor', _('First deputy mayor')),
        ('PRESIDENT', 'president', _('President')),
        ('VICE', 'vice', _('Vice president')),
        ('VICEVICE', 'vicevice', _('Vice vice president')),
                                      )

    charge = models.ForeignKey(InstitutionCharge, verbose_name=_('charge'))
    charge_type = models.CharField(_('charge type'), max_length=16, choices=CHARGE_TYPES)
    class Meta:
        verbose_name = _('institutional responsability')
        verbose_name_plural = _('institutional responsabilities')


class CompanyCharge(Charge):
    """
    This is a charge in a company controlled by the municipality (it: partecipate).
    """  
    CEO_CHARGE = 1
    PRES_CHARGE = 2
    VICE_CHARGE = 3
    DIR_CHARGE = 4
    CHARGE_TYPES = Choices(
        (CEO_CHARGE, _('Chief Executive Officer')),
        (PRES_CHARGE, _('President')),    
        (VICE_CHARGE, _('Vice president')),
        (DIR_CHARGE, _('Member of the board')),
    )
    
    company = models.ForeignKey('Company', on_delete=models.PROTECT, verbose_name=_('company'), related_name='charge_set')
    charge_type = models.IntegerField(_('charge type'), choices=CHARGE_TYPES)
    
    class Meta(Charge.Meta):
        db_table = u'people_organization_charge'
        verbose_name = _('organization charge')
        verbose_name_plural = _('organization charges')
    
    def __unicode__(self):
        # TODO: implement ``get_charge_type_display()`` method
        return u'%s - %s' % (self.get_charge_type_display(), self.company.name)
    
    
class AdministrationCharge(Charge):
    """
    This is a charge in the internal municipality administration.
    """
    DIR_CHARGE = 1
    EXEC_CHARGE = 2
    CHARGE_TYPES = Choices(
      (DIR_CHARGE, _('Director')),    
      (EXEC_CHARGE, _('Executive')),
    )
    
    office = models.ForeignKey('Office', on_delete=models.PROTECT, verbose_name=_('office'), related_name='charge_set')
    charge_type = models.IntegerField(_('charge type'), choices=CHARGE_TYPES)

    class Meta(Charge.Meta):
        db_table = u'people_administration_charge'
        verbose_name = _('administration charge')
        verbose_name_plural = _('administration charges')
    
    def __unicode__(self):
        # TODO: implement ``get_charge_type_display()`` method
        return u'%s - %s' % (self.get_charge_type_display(), self.office.name)
 

class Group(models.Model):
    """
    This model represents a group of counselors.
    """
    name = models.CharField(max_length=100)
    acronym = models.CharField(blank=True, max_length=16)
    charge_set = models.ManyToManyField('InstitutionCharge', through='GroupCharge')
    slug = models.SlugField(unique=True, blank=True, null=True, help_text=_('Suggested value automatically generated from name, must be unique'))

    img = ImageField(upload_to="group_images", blank=True, null=True)

    start_date = models.DateField(blank=True, null=True, verbose_name=_("start date"))
    end_date = models.DateField(blank=True, null=True, verbose_name=_("end date"))


    objects = PassThroughManager.for_queryset_class(GroupQuerySet)()


    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')
        ordering = ("name", "acronym", )

    def get_absolute_url(self):
        return reverse("om_institution_group", kwargs={'slug': self.slug})

    def __unicode__(self):
        if self.start_date:
            return u'%s (%s, %s)' % (self.name, self.acronym, self.start_date.year)
        else:
            return u'%s (%s)' % (self.name, self.acronym)

    @property
    def leader(self):
        """
        The current leader of the Group as GroupResponsability.
        None if not found.

        To fetch the InstitutionCharge, .groupcharge.charge.
        """
        try:
            leader = GroupResponsability.objects.select_related().get(
                charge__group=self,
                charge_type=GroupResponsability.CHARGE_TYPES.leader,
                end_date__isnull=True
            )
            return leader
        except ObjectDoesNotExist:
            return None

    @property
    def deputy(self):
        """
        The current deputy leader of the Group as GroupResponsability.
        None if not found.

        To fetch the InstitutionCharge, .groupcharge.charge.
        """
        try:
            deputy = GroupResponsability.objects.select_related().get(
                charge__group=self,
                charge_type=GroupResponsability.CHARGE_TYPES.deputy,
                end_date__isnull=True
            )
            return deputy
        except ObjectDoesNotExist:
            return None

    @property
    def members(self):
        """
        Current members of the group, as institution charges, leader and
        council president and vice presidents **excluded**.
        """
        group_members = self.groupcharge_set.current().exclude(
            groupresponsability__charge_type__in=(
                GroupResponsability.CHARGE_TYPES.leader,
                GroupResponsability.CHARGE_TYPES.deputy
                ),
            groupresponsability__end_date__isnull=True
        )

        return self.institution_charges.filter(groupcharge__in=group_members)

        """
        President and vice-president may be excluded
           .exclude(
            groupcharge__charge__institutionresponsability__charge_type__in=(
                InstitutionResponsability.CHARGE_TYPES.president,
                InstitutionResponsability.CHARGE_TYPES.vice
            )
        )
        """

    @property
    def alpha_members(self):
        """
        Alphabetically sorted members
        """
        return self.members.order_by('person__last_name')

    def get_institution_charges(self, moment=None):
        """
        All current institution charges in the group, leader **included**
        """
        return self.charge_set.all().current(moment=moment)
    institution_charges = property(get_institution_charges)

    @property
    def current_size(self):
        """
        returns number of current charges
        """
        return self.groupcharge_set.current().count()

    @property
    def is_current(self):
        """
        returns True if the group has at least one current charge
        """
        return self.groupcharge_set.current().count() > 0

    @property
    def majority_records(self):
        return self.groupismajority_set.all()

    @property
    def in_council_now(self):
        today = date.today()

        found = self.majority_records.filter(Q(end_date__gt=today) | Q(end_date__isnull=True))

        return found.count() > 0

    @property
    def is_majority_now(self):
        # only one majority record with no ``end_date`` (or with an ``end_date``
        # set in the future) should exists at a time (i.e. the current one)

        today = date.today()

        found = self.majority_records.filter(is_majority=True).exclude(end_date__lt=today)
        return found.count() > 0

    @property
    def resources(self):
        return self.resource_set.all()

class GroupCharge(models.Model):
    """
    This model records the historical composition of council groups. 
    
    This only makes sense for ``InstitutionCharges``.
    """
    group = models.ForeignKey('Group', verbose_name=_("group"))
    charge = models.ForeignKey('InstitutionCharge', verbose_name=_("charge"))
    charge_description = models.CharField(blank=True, max_length=255, verbose_name=_("charge description"))
    start_date = models.DateField(verbose_name=_("start date"))
    end_date = models.DateField(blank=True, null=True, verbose_name=_("end date"))
    end_reason = models.CharField(blank=True, max_length=255, verbose_name=_("end reason"))
    
    objects = PassThroughManager.for_queryset_class(TimeFramedQuerySet)()    

    @property
    def responsabilities(self):
        return self.groupresponsability_set.all()


    def get_current_responsability(self, moment=None):
        """
        Returns the current group responsability, if any
        """
        responsibility = None
        try:
            responsibility = self.responsabilities.current(moment=moment)[0]
        except IndexError:
            # no responsibility, nothing to do
            pass

        return responsibility
    current_responsability = property(get_current_responsability)


    @property
    def responsability(self):
        s = ""
        try:
            r = self.responsabilities[0]

            end_date = ""
    
            if r.end_date:
                end_date = " - %s" % r.end_date

            s = "%s: %s%s" % (r.get_charge_type_display(), r.start_date, end_date)
        except IndexError:
            # no responsibility
            pass

        return s

    class Meta:
        db_table = u'people_group_charge'
        verbose_name = _('group charge')
        verbose_name_plural = _('group charges')

    def __unicode__(self):
        if self.responsability:
            return u"%s - %s - %s" % (self.group.acronym, self.charge.person, self.responsability)
        else:
            return u"%s - %s" % (self.group.acronym, self.charge.person)

class GroupResponsability(ChargeResponsability):
    """
    Responsibility for group charges.
    """
    CHARGE_TYPES = Choices(
        ('LEADER', 'leader', _('Group leader')),
        ('DEPUTY', 'deputy', _('Group deputy leader')),
    )
    charge_type = models.CharField(_('charge type'), max_length=16, choices=CHARGE_TYPES)
    charge = models.ForeignKey(GroupCharge, verbose_name=_('charge'))


    def __unicode__(self):
    
        end_date = ""
    
        if self.end_date:
            end_date = " - %s" % self.end_date

        return u"%s (%s%s)" % (self.get_charge_type_display(), self.start_date, end_date)

    class Meta:
        verbose_name = _("group responsibility")
        verbose_name_plural = _("group responsibilities")


class GroupIsMajority(models.Model):
    """
    This model records the historical composition of the majority
    """
    group = models.ForeignKey('Group')
    is_majority = models.NullBooleanField(_('Is majority'), default=False, null=True)
    start_date = models.DateField(_('Start date'))
    end_date = models.DateField(_('End date'), blank=True, null=True)
    
    objects = PassThroughManager.for_queryset_class(TimeFramedQuerySet)() 

    class Meta:
        verbose_name = _('group majority')
        verbose_name_plural = _('group majorities')
    
    def __unicode__(self):
        if self.is_majority:
            return u'yes'
        elif self.is_majority is False:
            return u'no'
        else:
            return u'na'
            


#
# Bodies
#
class Body(SlugModel):
    """
    The base model for bodies. 
    
    Uses the *abstract base class* inheritance model.
    """
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True, help_text=_('Suggested value automatically generated from name, must be unique'))
    description = models.TextField(_('description'), blank=True)

    @property
    def lowername(self):
        return self.name.lower()

    class Meta:
        abstract = True
    
    def __unicode__(self):
        return u'%s' % (self.name,)
    
  
  
class Institution(Body):
    """
    Institutional bodies can be of different types (as specified by the ``institution_type`` field).
    
    This model has a relation with itself, in order to map hierarchical bodies (joint committees, ...).
    """
    MAYOR = 1
    CITY_GOVERNMENT = 2
    COUNCIL = 3
    COMMITTEE = 4
    JOINT_COMMITTEE = 5

    INSTITUTION_TYPES = Choices(
      (MAYOR, _('Mayor')),    
      (COUNCIL, _('Council')),
      (CITY_GOVERNMENT, _('Town government')),
      (COMMITTEE, _('Committee')),
      (JOINT_COMMITTEE, _('Joint committee')),
    )
    
    parent = models.ForeignKey('Institution', related_name='sub_body_set', blank=True, null=True)
    institution_type = models.IntegerField(choices=INSTITUTION_TYPES)
    position = models.PositiveIntegerField(editable=False, default=0)
    
    class Meta(Body.Meta):
        verbose_name = _('institution')
        verbose_name_plural = _('institutions')
        ordering = ('position',)
    
    def save(self, *args, **kwargs):
        """slugify name on first save"""
        if not self.id:
            self.slug = slugify(self.name)
            # set position
            qs = self.__class__.objects.order_by('-position')
            try:
                self.position = qs[0].position + 1
            except IndexError:
                self.position = 0
        super(Institution, self).save(*args, **kwargs)
        
    def get_absolute_url(self):
        if self.institution_type == self.MAYOR:
            return reverse("om_institution_mayor")
        elif self.institution_type == self.CITY_GOVERNMENT:
            return reverse("om_institution_citygov")
        elif self.institution_type == self.COUNCIL:
            return reverse("om_institution_council")
        elif self.institution_type == self.COMMITTEE:
            return reverse("om_institution_committee", kwargs={'slug': self.slug})

    @property
    def sittings(self):
        """
        A Sitting is linked to an Institution trhough fields "institution" and
        "other_institution". The related name of the former is "sitting_set",
        while the related name of the latter is "other_sittings". If you want to 
        know all the sittings of this Institution you must take the (distinct) 
        union of the two
        """
        qs = (self.sitting_set.all() | self.other_sittings.all()).distinct()

        return qs

    @property
    def name_with_preposition(self):
        """
        returns name with preposition
        """
        if self.institution_type == self.MAYOR:
            return "del %s" % self.name
        elif self.institution_type == self.CITY_GOVERNMENT:
            return "della %s" % self.name
        elif self.institution_type == self.COUNCIL:
            return "del %s" % self.name
        elif self.institution_type == self.COMMITTEE:
            return "della %s" % self.name

        return self.name

    @property
    def charges(self):
        """
        The QuerySet of all *current* charges (``InstitutionCharge`` instances) 
        associated with this institution.
        """
        return self.get_current_charges(moment=None)

    def get_current_charges(self, moment=None):
        """
        The WS of all charges current at the specified moment
        """
        return self.charge_set.all().current(moment)


    @property
    def firstdeputy(self):
        """
        The current firstdeputy mayor of the institution as InstitutionResponsability.
        None if not found.

        To access the charge: firstdeputy.charge
        """
        try:
            return InstitutionResponsability.objects.select_related().get(
                charge__institution=self,
                charge_type=InstitutionResponsability.CHARGE_TYPES.firstdeputymayor,
                end_date__isnull=True
            )
        except ObjectDoesNotExist:
            return None

    @property
    def president(self):
        """
        The current president of the institution as InstitutionResponsability.
        None if not found.

        To access the charge: pres.charge
        """
        try:
            pres = InstitutionResponsability.objects.select_related().get(
                charge__institution=self,
                charge_type=InstitutionResponsability.CHARGE_TYPES.president,
                end_date__isnull=True
            )
            return pres
        except ObjectDoesNotExist:
            return None


    @property
    def vicepresidents(self):
        """
        The current vice presidents of the institution, as InstitutionResponsabilities

        There can be more than one vicepresident.

        To access the charge: vp.charge
        """
        return InstitutionResponsability.objects.select_related().filter(
            charge__institution=self,
            charge_type=InstitutionResponsability.CHARGE_TYPES.vice,
            end_date__isnull=True
        )

    @property
    def members(self):
        """
        Members of the institution, as charges.
        Current mayor, first deputy, president and vice presidents **excluded**.
        """
        return self.charges.exclude(
            institutionresponsability__charge_type__in=(
                InstitutionResponsability.CHARGE_TYPES.mayor,
                InstitutionResponsability.CHARGE_TYPES.firstdeputymayor,
                InstitutionResponsability.CHARGE_TYPES.president,
                InstitutionResponsability.CHARGE_TYPES.vice,
                ),
            institutionresponsability__end_date__isnull=True
        ).select_related()


    @property
    def emitted_acts(self):
        """
        The QuerySet of all acts emitted by this institution.
        
        Note that the objects comprising the resulting QuerySet aren't generic ``Act`` instances,
        but instances of specific ``Act`` subclasses (i.e. ``Deliberation``, ``Motion``, etc.).
        This is made possible by the fact that the default manager for the ``Act`` model is 
        ``model_utils.managers.InheritanceManager``, and this manager class declares 
        ``use_for_related_fields = True``.   See `Django docs`_ for details.
        
        .. _`Django docs`: https://docs.djangoproject.com/en/1.3/topics/db/managers/#controlling-automatic-manager-types
        """
        # NOTE: See also Django bug #14891
        return self.emitted_act_set.all().select_subclasses()

    @property
    def resources(self):
        return self.resource_set.all()

    @transaction.commit_on_success
    def _move(self, up):
        """
        To move an object requires, potentially, to update all the list of objects.
        In fact, we cannot assume that the position arguments are all consecutive.
        Doing some insertions and deletions it is possible to create "bubbles" and
        duplicates for the position values. The sorting algorithms goes like this:

        - assign everyone a consecutive and unique position value
        - detect the previous and next institution, w.r.t. self
        - if up, switch position with previous and save previous
        - if down, switch position with next and save next
        - save self
        """
        qs = self.__class__._default_manager

        qs.order_by("position")

        p = 0
        prev_inst = None
        next_inst = None
        found = False
        for curr_inst in qs.all():
 
            found = found or (curr_inst == self)

            if curr_inst.position != p:
                curr_inst.position = p
                curr_inst.save()

            p = p + 1

            if not found:
                prev_inst = curr_inst
            elif next_inst is None and curr_inst != self:
                next_inst = curr_inst

        if up:
            if prev_inst:
                prev_inst.position,self.position = self.position,prev_inst.position
                prev_inst.save()
        else:
            if next_inst:

                next_inst.position,self.position = self.position,next_inst.position
                next_inst.save()

        self.save()

    def move_down(self):
        """
        Move this object down one position.
        """
        return self._move(up=False)

    def move_up(self):
        """
        Move this object up one position.
        """
        return self._move(up=True)
    

class Company(Body):
    """
    A company owned by the municipality, whose executives are nominated politically.
    """
    class Meta(Body.Meta):
        verbose_name = _('company')
        verbose_name_plural = _('companies')

    def get_absolute_url(self):
        return reverse("om_company_detail", kwargs={'slug': self.slug})
    
    @property
    def charges(self):
        """
        The QuerySet of all *current* charges (``CompanyCharge`` instances) 
        associated with this company.  
        """
        return self.charge_set.current()
 
    
  
class Office(Body):
    """
    Internal municipality office, playing a role in municipality's administration.
    """

    parent = models.ForeignKey('Office', blank=True, null=True, default=None, verbose_name=_("the parent office, in a hierarchy"))

    class Meta(Body.Meta):
        verbose_name = _('office')
        verbose_name_plural = _('offices')

    def get_abolute_url(self):
        return reverse("om_office_detail", kwargs={'slug': self.slug})
    
    @property
    def charges(self):
        """
        The QuerySet of all *current* charges (``AdministrationCharge`` instances) 
        associated with this office.  
        """
        return self.charge_set.current()


#
# Sittings
#
class Sitting(TimeStampedModel):
    """
    A sitting models a gathering of people in a give institution.

    Usually votations and speeches occur, during a sitting.

    A sitting is broken down into SittingItems, and each item may be related to one or more acts.
    Each item contains Speeches, which are a very special extension of Document
    (audio attachments, with complex relations with votations, charges and acts).
    """
    idnum = models.CharField(blank=True, max_length=64, verbose_name=_("identifier"))
    date = models.DateField(verbose_name=_("date"))
    number = models.IntegerField(blank=True, null=True, verbose_name=_("number"))
    call = models.IntegerField(blank=True, null=True, verbose_name=_("call"))
    institution = models.ForeignKey(Institution, on_delete=models.PROTECT, verbose_name=_("institution"))
    other_institution_set = models.ManyToManyField(Institution, blank=True, null=True, verbose_name=_("other institutions"), related_name="other_sittings")

    minute = models.ForeignKey('acts.Minute', null=True, blank=True, related_name="sitting_set", verbose_name=_("minute"))

    class Meta:
        verbose_name = _('sitting')
        verbose_name_plural = _('sittings')
    
    def __unicode__(self):

        num = ""
        if self.number:
            num = " num. %s " % self.number

        return u'Seduta %s del %s (%s)' % (num, self.date.strftime('%d/%m/%Y'), self.institution.name)

    @property
    def other_institutions(self):
        return self.other_institution_set.all()

    @property
    def institutions(self):
        qs = Institution.objects.none()

        if self.institution_id != None:
            qs = Institution.objects.filter(id=self.institution_id)

        qs = (qs | self.other_institution_set.all()).distinct()

        return qs
        
     
    @property
    def sitting_items(self):
        return SittingItem.objects.filter(sitting=self)

    @property
    def num_items(self):
        return self.sitting_items.count()

    @permalink
    def get_absolute_url(self):
        prefix = "%s-%s-%s" % (self.institution.slug, self.idnum, self.date, )
        sitting_url = 'om_sitting_detail', (), { 'prefix':prefix, 'pk':self.pk, }
        return sitting_url

    @property
    def sitting_next(self):
        next = Sitting.objects.filter(date__gt=self.date,institution=self.institution).order_by("date")[:1]

        if len(next) == 0:
            return None
        else:
            return next[0]

    @property
    def sitting_prev(self):
        prev = Sitting.objects.filter(date__lt=self.date,institution=self.institution).order_by("-date")[:1]
        
        if len(prev) == 0:
            return None
        else:
            return prev[0]

class SittingItem(models.Model):
    """
    A SittingItem maps a single point of discussion in a Sitting.

    It can be of type:
    - odg - a true items of discussion
    - procedural - a procedural issue, discussed, mostly less relevant
    - intt - interrogations and interpellances (questions and answers), usually discussed at the beginning of the sitting

    SittingItems are ordered through the seq_order field.
    """

    ITEM_TYPE = Choices(
        ('ODG', 'odg', _('ordine del giorno')),
        ('PROC', 'procedural', _('questione procedurale')),
        ('INTT', 'intt', _('interrogation')),
    )

    sitting = models.ForeignKey(Sitting)
    title = models.CharField(max_length=512)
    item_type = models.CharField(choices=ITEM_TYPE, max_length=4)
    seq_order = models.IntegerField(default=0,verbose_name=_('seq_order'))
    related_act_set = models.ManyToManyField('acts.Act', blank=True, null=True)

    class Meta:
        verbose_name = _('sitting item')
        verbose_name_plural = _('sitting items')

    def __unicode__(self):
        return unicode(self.title)

    @permalink
    def get_absolute_url(self):
        return 'om_sittingitem_detail', (), { 'pk': self.pk }

    @property
    def num_related_acts(self):
        return self.related_act_set.count()


    @property
    def long_repr(self):
        """
        long unicode representation, contains the sitting details
        """
        return u'%s - %s' % (self.sitting, self)

    @property
    def num_speeches(self): 
        """
        the amount of speeches that refer to this sitting item
        """
        return open_municipio.acts.models.Speech.objects.filter(sitting_item=self).count()

## Private DB access API

class Mayor(object):
    """
    A municipality mayor (both as a charge and an institution).
    """
     
    _my_institution = None
    
    @property
    def as_institution(self):
        """
        A municipality mayor, as an *institution*.
        """
 
        if Mayor._my_institution is None:       

            try:
                Mayor._my_institution = Institution.objects.select_related().get(institution_type=Institution.MAYOR)
            except Institution.DoesNotExist:
                # mayor does not exist, currently
                pass

        return Mayor._my_institution
    
    @property
    def as_charge(self):
        """
        A municipality mayor, as a *charge*.
        """
        mayor = None

        try:
            mayor = InstitutionCharge.objects.select_related().filter(end_date__isnull=True).get(institution__institution_type=Institution.MAYOR)

        except InstitutionCharge.DoesNotExist:
            # mayor has not been created
            pass

        return mayor
    
    @property
    def acts(self):
        """
        The QuerySet of all acts emitted by the mayor (as an institution).
        
        Note that the objects comprising the resulting QuerySet aren't generic ``Act`` instances,
        but instances of specific ``Act`` subclasses (i.e. ``Deliberation``, ``Motion``, etc.).
        """
        return self.as_institution.emitted_acts
    

class CityCouncil(object):

    _my_institution = None

    @property
    def as_institution(self):
        """
        A municipality council, as an *institution*.
        """

        if CityCouncil._my_institution is None:

            try:
                CityCouncil._my_institution = Institution.objects.get(institution_type=Institution.COUNCIL)
            except Institution.DoesNotExist:
                # the city council has not been created
                pass
        
        return CityCouncil._my_institution
    
    @property
    def charges(self):
        """
        All current members of the municipality council (aka *counselors*), as charges.
        President and vice-presidents **included**.
        """
        charges = InstitutionCharge.objects.none()

        if self.as_institution:
            charges = self.as_institution.charges.select_related()
    
        return charges

    @property
    def president(self):
        """
        The current president of the city council as InstitutionResponsability
        None if not found.
        """
        president = None
    
        if self.as_institution:
            president = self.as_institution.president

        return president


    @property
    def vicepresidents(self):
        """
        The current vice presidents of the city council, as InstitutionResponsabilities

        There can be more than one vicepresident
        """

        vp = None

        if self.as_institution:
            vp = self.as_institution.vicepresidents.select_related()

        return vp


    @property
    def members(self):
        """
        Members of the municipality council (aka *counselors*), as charges.
        Current president and vice presidents **excluded**.
        """
        members = InstitutionCharge.objects.none()

        if self.as_institution:
            members = self.as_institution.members.select_related()

        return members

    @property
    def majority_members(self):
        """
        Majority counselors, as charges.
        """
        # FIXME: this method should return a QuerySet, non a Set
        result = set()
        for majority_group in self.majority_groups:
            result.add(majority_group.counselors)            
        return result
    
    @property
    def minority_members(self):
        """
        Minority counselors, as charges.
        """
        # FIXME: this method should return a QuerySet, non a Set
        result = set()
        for minority_group in self.minority_groups:
            result.add(minority_group.counselors)            
        return result
        
    @property
    def groups(self):
        """
        Groups of counselors within of a municipality council.
        """
        return Group.objects.select_related().all()
    
    @property
    def majority_groups(self):
        """
        Counselors' groups belonging to majority.
        """
        qs = Group.objects.select_related().filter(groupismajority__end_date__isnull=True).filter(groupismajority__is_majority=True)
        return qs
    
    @property
    def minority_groups(self):
        """
        Counselors' groups belonging to minority.
        """
        qs = Group.objects.select_related().filter(groupismajority__end_date__isnull=True).filter(groupismajority__is_majority=False)
        return qs

    @property
    def acts(self):
        """
        The QuerySet of all acts emitted by the City Council.
        
        Note that the objects comprising the resulting QuerySet aren't generic ``Act`` instances,
        but instances of specific ``Act`` subclasses (i.e. ``Deliberation``, ``Motion``, etc.).
        """
        return self.as_institution.select_related().emitted_acts
    
    @property
    def deliberations(self):
        """
        The QuerySet of all deliberations emitted by the City Council.
        """
        from open_municipio.acts.models import Deliberation
        return Deliberation.objects.select_related().filter(emitting_institution=self.as_institution)
    
    @property
    def interrogations(self):
        """
        The QuerySet of all interrogations emitted by the City Council.
        """
        from open_municipio.acts.models import Interrogation
        return Interrogation.objects.select_related().filter(emitting_institution=self.as_institution)
    
    @property
    def interpellations(self):
        """
        The QuerySet of all interpellations emitted by the City Council.
        """
        from open_municipio.acts.models import Interpellation
        return Interpellation.objects.select_related().filter(emitting_institution=self.as_institution)
            
    @property
    def motions(self):
        """
        The QuerySet of all motions emitted by the City Council.
        """
        from open_municipio.acts.models import Motion
        return Motion.objects.select_related().filter(emitting_institution=self.as_institution)
    
    @property
    def agendas(self):
        """
        The QuerySet of all agendas emitted by the City Council.
        """
        from open_municipio.acts.models import Agenda
        return Agenda.objects.select_related().filter(emitting_institution=self.as_institution)
    
    @property
    def amendments(self):
        """
        The QuerySet of all amendments emitted by the City Council.
        """
        from open_municipio.acts.models import Amendment
        return Amendment.objects.select_related().filter(emitting_institution=self.as_institution)


class CityGovernment(object):

    _my_institution = None

    @property
    def as_institution(self):
        """
        A municipality government, as an *institution*.
        """

        if CityGovernment._my_institution is None:

            try:
                CityGovernment._my_institution = Institution.objects.get(institution_type=Institution.CITY_GOVERNMENT)
            except Institution.DoesNotExist:
                # city gov has not been created, yet
                pass

        return CityGovernment._my_institution
    
    @property
    def charges(self):
        """
        Members of a municipality government (mayor and first deputy included), as charges.
        """
        return self.as_institution.charges.select_related()

    @property
    def firstdeputy(self):
        """
        Returns the first deputy mayor, if existing, None if not existing
        """
        firstdeputy = None

        if self.as_institution:
            firstdeputy = self.as_institution.firstdeputy

        return firstdeputy

    @property
    def members(self):
        """
        Members of a municipality government (mayor and first deputy excluded), as charges.
        """

        members = InstitutionCharge.objects.none()
    
        if self.as_institution:
            members = self.as_institution.members.select_related()

        return members

    @property
    def acts(self):
        """
        The QuerySet of all acts emitted by the city government (as an institution).
        
        Note that the objects comprising the resulting QuerySet aren't generic ``Act`` instances,
        but instances of specific ``Act`` subclasses (i.e. ``Deliberation``, ``Motion``, etc.).
        """
        return self.as_institution.emitted_acts
    
    @property
    def deliberations(self):
        """
        The QuerySet of all deliberations emitted by the City Government.
        """
        from open_municipio.acts.models import Deliberation
        return Deliberation.objects.select_related().filter(emitting_institution=self.as_institution)
    
    @property
    def interrogations(self):
        """
        The QuerySet of all interrogations emitted by the City Government.
        """
        from open_municipio.acts.models import Interrogation
        return Interrogation.objects.select_related().filter(emitting_institution=self.as_institution)
    
    @property
    def interpellations(self):
        """
        The QuerySet of all interpellations emitted by the City Government.
        """
        from open_municipio.acts.models import Interpellation
        return Interpellation.objects.select_related().filter(emitting_institution=self.as_institution)
            
    @property
    def motions(self):
        """
        The QuerySet of all motions emitted by the City Government.
        """
        from open_municipio.acts.models import Motion
        return Motion.objects.select_related().filter(emitting_institution=self.as_institution)
    
    @property
    def agendas(self):
        """
        The QuerySet of all agendas emitted by the City Government.
        """
        from open_municipio.acts.models import Agenda
        return Agenda.objects.select_related().filter(emitting_institution=self.as_institution)
    
    @property
    def amendments(self):
        """
        The QuerySet of all amendments emitted by the City Government.
        """
        from open_municipio.acts.models import Amendment
        return Amendment.objects.select_related().filter(emitting_institution=self.as_institution)


class Committees(object):

    def as_institution(self):
        """
        Municipality committees, as *institutions*.
        """
        # FIXME: Should we include joint committees here?
        # (Institution.JOINT_COMMITTEE)
        return Institution.objects.select_related().filter(
            institution_type__in=(Institution.COMMITTEE, Institution.JOINT_COMMITTEE)
        )



class Municipality(object):
    """
    A hierarchy of objects representing a municipality.
    
    Provides convenient access to insitutions, charges, groups and the like.
    """  
    def __init__(self):
        self.mayor = Mayor()
        self.gov = CityGovernment()
        self.council = CityCouncil()
        self.committees = Committees()
  
  
municipality = Municipality()
