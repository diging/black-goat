"""goat URL Configuration
"""
from django.conf.urls import include, url
from django.contrib import admin
admin.autodiscover()
from django.contrib.auth.views import login

from rest_framework import routers

from goat import views

router = routers.DefaultRouter()
router.register(r'authority', views.AuthorityViewSet)
router.register(r'concept', views.ConceptViewSet)
router.register(r'identity', views.IdentityViewSet)
router.register(r'identitysystem', views.IdentitySystemViewSet)



urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', views.home, name="home"),
    url(r'^search/$', views.search, name="search"),
    url(r'^search/([a-zA-Z0-9\-]+)', views.search_results, name='search-results'),

    url(r'^', include(router.urls)),
    url(r'^login/$', login, {'template_name': 'admin/login.html'}, name="login"),
    url('^', include('django.contrib.auth.urls')),

]
