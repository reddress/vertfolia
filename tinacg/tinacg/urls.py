from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'tinacg.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

                       url(r'^$', 'tinacg.views.index', name='tina_index'),
                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^vertfolia/', include('vertfolia.urls')),
                           
)

urlpatterns = urlpatterns + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
