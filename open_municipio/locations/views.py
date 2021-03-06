# -*- coding: utf-8 -*-

from django.views.generic import DetailView, FormView, ListView
from django.utils.decorators import method_decorator
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.db.models import Q

from django.contrib.auth.decorators import user_passes_test


from open_municipio.acts.models import ( Act, Deliberation, CGDeliberation, Motion, Agenda,
                                         Interrogation, Interpellation, Amendment, Audit )

from open_municipio.locations.models import Location, TaggedActByLocation
from open_municipio.locations.forms import ActLocationsAddForm
from open_municipio.taxonomy.models import Category
from open_municipio.taxonomy.views import TopicDetailView


class LocationDetailView(TopicDetailView):

    model = Location
    topic_type = 'location'

    def take_subtopics(self):
        return Location.objects.exclude(pk=self.object.pk)


class LocationListView(ListView):
    
    model = Location
    context_object_name = 'subtopics'

    def get_context_data(self, *args, **kwargs):

        context = super(LocationListView, self).get_context_data(*args, **kwargs)

        context["topic"] = "Territorio"
        context["topics"] = Category.objects.all()

        context['n_acts'] = Act.objects.exclude(location_set=None).count()

        act_types = [Deliberation, CGDeliberation, Motion, Agenda, \
            Interrogation, Interpellation, Audit, Amendment]

        for act_type in act_types:
            key = 'n_' + act_type.__name__.lower() + 's'
            key_nonfinal = key + '_nonfinal'
            context[key_nonfinal] = act_type.objects.exclude(location_set=None).filter(~ Q(status__in=(s[0] for s in act_type.FINAL_STATUSES))).count()
            context[key] = act_type.objects.exclude(location_set=None).count()

        context['facets'] = '&f=has_locations:sì'

        return context


class ActTagByLocationView(FormView):
    form_class = ActLocationsAddForm
        
    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        return super(ActTagByLocationView, self).dispatch(*args, **kwargs)
    
    def get_object(self):
        act = get_object_or_404(Act, pk=self.kwargs['pk'])
        return act
    
    def form_valid(self, form):
        # clear any existing location-based taxonomy for this act
        TaggedActByLocation.objects.filter(act=self.act).delete()
        # record new taxonomy, including tagging metadata (tagger, tagging time, ..)
        for location in form.cleaned_data['locations']:
            TaggedActByLocation.objects.create(act=self.act, location=location, tagger=self.request.user)
            
        return HttpResponseRedirect(self.get_success_url())
       
    def form_invalid(self, form=None):
        return HttpResponseBadRequest("%s" % form)
    
    def get_success_url(self):
        return self.act.downcast().get_absolute_url()
    
    def post(self, request, *args, **kwargs):
        self.act = self.get_object()
        form = self.form_class(data=self.request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
