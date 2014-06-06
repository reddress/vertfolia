from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
                       url(r'^$', views.index, name='index'),
                       url(r'^add_transaction/$', views.add_transaction,
                           name='add_transaction'),
                       )
