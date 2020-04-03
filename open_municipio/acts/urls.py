from django.conf.urls import patterns, url

from open_municipio.acts.views import (ActSearchView, AgendaDetailView,
                DeliberationDetailView, InterpellationDetailView,
                InterrogationDetailView, MotionDetailView, AmendmentDetailView,
                ActTransitionAddView, ActTransitionRemoveView, ActTagEditorView, 
                ActLiveEditView, RecordVoteOnActView, CGDeliberationDetailView,
                SpeechSearchView, SpeechDetailView, 
                DecisionDetailView, DecreeDetailView, AuditDetailView, MinuteDetailView, )

from open_municipio.locations.views import ActTagByLocationView

urlpatterns = patterns('',
    # faceted navigation
    url(r'^$', ActSearchView(template='acts/act_search.html'), name='om_act_search'), 
    # agendas (old urls, pk)
    url(r'^agendas/(?P<pk>\d+)/$', AgendaDetailView.as_view(),  name='om_agenda_detail'),
    url(r'^agendas/(?P<pk>\d+)/(?P<tab>documents)/$', AgendaDetailView.as_view(),  name='om_agenda_detail_documents'),
    url(r'^agendas/(?P<pk>\d+)/(?P<tab>amendments)/$', AgendaDetailView.as_view(),  name='om_agenda_detail_amendments'),
    # agendas
    url(r'^agendas/(?P<slug>[\w\-]+)/$', AgendaDetailView.as_view(),  name='om_agenda_detail'),
    url(r'^agendas/(?P<slug>[\w\-]+)/(?P<tab>documents)/$', AgendaDetailView.as_view(),  name='om_agenda_detail_documents'),
    url(r'^agendas/(?P<slug>[\w\-]+)/(?P<tab>amendments)/$', AgendaDetailView.as_view(),  name='om_agenda_detail_amendments'),

    # cg-deliberations (old urls, pk)
    url(r'^cgdeliberations/(?P<pk>\d+)/$', CGDeliberationDetailView.as_view(),  name='om_cgdeliberation_detail'),
    url(r'^cgdeliberations/(?P<pk>\d+)/(?P<tab>documents)/$', CGDeliberationDetailView.as_view(),  name='om_cgdeliberation_detail_documents'),
    url(r'^cgdeliberations/(?P<pk>\d+)/(?P<tab>amendments)/$', CGDeliberationDetailView.as_view(),  name='om_cgdeliberation_detail_amendments'),
    # cg-deliberations
    url(r'^cgdeliberations/(?P<slug>[\w\-]+)/$', CGDeliberationDetailView.as_view(),  name='om_cgdeliberation_detail'),
    url(r'^cgdeliberations/(?P<slug>[\w\-]+)/(?P<tab>documents)/$', CGDeliberationDetailView.as_view(),  name='om_cgdeliberation_detail_documents'),
    url(r'^cgdeliberations/(?P<slug>[\w\-]+)/(?P<tab>amendments)/$', CGDeliberationDetailView.as_view(),  name='om_cgdeliberation_detail_amendments'),


    # deliberations (old urls, pk)
    url(r'^deliberations/(?P<pk>\d+)/$', DeliberationDetailView.as_view(),  name='om_deliberation_detail'),
    url(r'^deliberations/(?P<pk>\d+)/(?P<tab>documents)/$', DeliberationDetailView.as_view(),  name='om_deliberation_detail_documents'),
    url(r'^deliberations/(?P<pk>\d+)/(?P<tab>amendments)/$', DeliberationDetailView.as_view(),  name='om_deliberation_detail_amendments'),
    # deliberations
    url(r'^deliberations/(?P<slug>[\w\-]+)/$', DeliberationDetailView.as_view(),  name='om_deliberation_detail'),
    url(r'^deliberations/(?P<slug>[\w\-]+)/(?P<tab>documents)/$', DeliberationDetailView.as_view(),  name='om_deliberation_detail_documents'),
    url(r'^deliberations/(?P<slug>[\w\-]+)/(?P<tab>amendments)/$', DeliberationDetailView.as_view(),  name='om_deliberation_detail_amendments'),

    # interpellations (old urls, pk)
    url(r'^interpellations/(?P<pk>\d+)/$', InterpellationDetailView.as_view(),  name='om_interpellation_detail'),
    url(r'^interpellations/(?P<pk>\d+)/(?P<tab>documents)/$', InterpellationDetailView.as_view(),  name='om_interpellation_detail_documents'),
    url(r'^interpellations/(?P<pk>\d+)/(?P<tab>amendments)/$', InterpellationDetailView.as_view(),  name='om_interpellation_detail_amendments'),
    # interpellations
    url(r'^interpellations/(?P<slug>[\w,\-]+)/$', InterpellationDetailView.as_view(),  name='om_interpellation_detail'),
    url(r'^interpellations/(?P<slug>[\w,\-]+)/(?P<tab>documents)/$', InterpellationDetailView.as_view(),  name='om_interpellation_detail_documents'),
    url(r'^interpellations/(?P<slug>[\w,\-]+)/(?P<tab>amendments)/$', InterpellationDetailView.as_view(),  name='om_interpellation_detail_amendments'),

    # interrogations (old urls, pk)
    url(r'^interrogations/(?P<pk>\d+)/$', InterrogationDetailView.as_view(),  name='om_interrogation_detail'),
    url(r'^interrogations/(?P<pk>\d+)/(?P<tab>documents)/$', InterrogationDetailView.as_view(),  name='om_interrogation_detail_documents'),
    url(r'^interrogations/(?P<pk>\d+)/(?P<tab>amendments)/$', InterrogationDetailView.as_view(),  name='om_interrogation_detail_amendments'),
    # interrogations
    url(r'^interrogations/(?P<slug>[\w,\-]+)/$', InterrogationDetailView.as_view(),  name='om_interrogation_detail'),
    url(r'^interrogations/(?P<slug>[\w,\-]+)/(?P<tab>documents)/$', InterrogationDetailView.as_view(),  name='om_interrogation_detail_documents'),
    url(r'^interrogations/(?P<slug>[\w,\-]+)/(?P<tab>amendments)/$', InterrogationDetailView.as_view(),  name='om_interrogation_detail_amendments'),

    # motions (old urls, pk)
    url(r'^motions/(?P<pk>\d+)/$', MotionDetailView.as_view(),  name='om_motion_detail'),
    url(r'^motions/(?P<pk>\d+)/(?P<tab>documents)/$', MotionDetailView.as_view(),  name='om_motion_detail_documents'),
    url(r'^motions/(?P<pk>\d+)/(?P<tab>amendments)/$', MotionDetailView.as_view(),  name='om_motion_detail_amendments'),
    # motions
    url(r'^motions/(?P<slug>[\w\-]+)/$', MotionDetailView.as_view(),  name='om_motion_detail'),
    url(r'^motions/(?P<slug>[\w\-]+)/(?P<tab>documents)/$', MotionDetailView.as_view(),  name='om_motion_detail_documents'),
    url(r'^motions/(?P<slug>[\w\-]+)/(?P<tab>amendments)/$', MotionDetailView.as_view(),  name='om_motion_detail_amendments'),

    # amendments (old urls, pk)
    url(r'^amendments/(?P<pk>\d+)/$', AmendmentDetailView.as_view(),  name='om_amendment_detail'),
    url(r'^amendments/(?P<pk>\d+)/(?P<tab>documents)/$', AmendmentDetailView.as_view(),  name='om_amendment_detail_documents'),
    url(r'^amendments/(?P<pk>\d+)/(?P<tab>amendments)/$', AmendmentDetailView.as_view(),  name='om_amendment_detail_amendments'),
    # amendments
    url(r'^amendments/(?P<slug>[\w\-]+)/$', AmendmentDetailView.as_view(),  name='om_amendment_detail'),
    url(r'^amendments/(?P<slug>[\w\-]+)/(?P<tab>documents)/$', AmendmentDetailView.as_view(),  name='om_amendment_detail_documents'),
    url(r'^amendments/(?P<slug>[\w\-]+)/(?P<tab>amendments)/$', AmendmentDetailView.as_view(),  name='om_amendment_detail_amendments'),

    # decisions
    url(r'^decisions/(?P<slug>[\w\-]+)/$', DecisionDetailView.as_view(), name='om_decision_detail'),
    url(r'^decisions/(?P<slug>[\w\-]+)/(?P<tab>documents)/$', DecisionDetailView.as_view(),  name='om_decision_detail_documents'),
    url(r'^decisions/(?P<slug>[\w\-]+)/(?P<tab>amendments)/$', DecisionDetailView.as_view(),  name='om_decision_detail_amendments'),

    # decrees
    url(r'^decrees/(?P<slug>[\w\-]+)/$', DecreeDetailView.as_view(), name='om_decree_detail'),
    url(r'^decrees/(?P<slug>[\w\-]+)/(?P<tab>documents)/$', DecreeDetailView.as_view(),  name='om_decree_detail_documents'),
    url(r'^decrees/(?P<slug>[\w\-]+)/(?P<tab>amendments)/$', DecreeDetailView.as_view(),  name='om_decree_detail_amendments'),

    # audits
    url(r'^audits/(?P<slug>[\w\-]+)/$', AuditDetailView.as_view(), name='om_audit_detail'),
    url(r'^audits/(?P<slug>[\w\-]+)/(?P<tab>documents)/$', AuditDetailView.as_view(),  name='om_audit_detail_documents'),
    url(r'^audits/(?P<slug>[\w\-]+)/(?P<tab>amendments)/$', AuditDetailView.as_view(),  name='om_audit_detail_amendments'),

    # minute
    url(r'^minute/(?P<slug>[\w\-]+)/$', MinuteDetailView.as_view(), name='om_minute_detail'),
    url(r'^minute/(?P<slug>[\w\-]+)/(?P<tab>documents)/$', MinuteDetailView.as_view(),  name='om_minute_detail_documents'),
    url(r'^minute/(?P<slug>[\w\-]+)/(?P<tab>amendments)/$', MinuteDetailView.as_view(),  name='om_minute_detail_amendments'),
)

## Tag management
urlpatterns += patterns('',
    url(r'^(?P<pk>\d+)/topics/update/$', ActTagEditorView.as_view(),  name='om_act_topics_update'),
)

## Location management
urlpatterns += patterns('',
    url(r'^(?P<pk>\d+)/locations/add/$', ActTagByLocationView.as_view(),  name='om_act_locations_add'),
)

## Act's fields update
urlpatterns += patterns('',
    url(r'^(?P<pk>\d+)/description/update/$', ActLiveEditView.as_view(), name='om_act_description_update'),
    url(r'^(?P<pk>\d+)/title/update/$', ActLiveEditView.as_view(), name='om_act_title_update'),
)

## Transition management
urlpatterns += patterns('',
    url(r'(?P<pk>\d+)/transition/add/', ActTransitionAddView.as_view(), name='om_act_transition_add'),
    url(r'(?P<pk>\d+)/transition/remove/', ActTransitionRemoveView.as_view(), name='om_act_transition_remove'),
)

## Votes casted by users
urlpatterns += patterns('',
    url(r'^(?P<pk>\d+)/vote/(?P<direction>up|down|clear)/$', RecordVoteOnActView.as_view(), name='om_act_record_user_vote'),
)                        


urlpatterns += patterns('',
    # faceted navigation
    url(r'^speech/$', SpeechSearchView(template='acts/speech_search.html'),name='om_speech_search'),
    url(r'^speech/(?P<pk>\d+)/$', SpeechDetailView.as_view(),name='om_speech_detail'),
    url(r'^speech/(?P<slug>[\w\-]+)/$', SpeechDetailView.as_view(),name='om_speech_detail'),

)
