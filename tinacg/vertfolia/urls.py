from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
                       url(r'^$', views.index, name='index'),
                       url(r'^add_transaction/$', views.add_transaction,
                           name='add_transaction'),
                       url(r'^update_tree/$', views.update_tree,
                           name='update_tree'),
                       url(r'^view_transactions/$', views.view_transactions,
                           name='view_transactions'),
                       url(r'^view_latest_transactions/$',
                           views.view_latest_transactions,
                           name='view_latest_transactions'),
                       )
