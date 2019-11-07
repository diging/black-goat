"""goat URL Configuration
"""
from django.conf.urls import url
from django.urls import include, path, re_path
from django.contrib import admin
admin.autodiscover()
from django.contrib.auth import login

from rest_framework import routers

from goat import views

router = routers.DefaultRouter()
router.register(r'authority', views.AuthorityViewSet)
router.register(r'concept', views.ConceptViewSet)
router.register(r'identity', views.IdentityViewSet)
router.register(r'identitysystem', views.IdentitySystemViewSet)


urlpatterns = [
    url(r'^$', views.home, name="home"),
    path('admin/', admin.site.urls),
    url(r'^search/$', views.search, name="search"),
    url(r'^search/([a-zA-Z0-9\-]+)', views.search_results, name='search-results'),
    url(r'^retrieve/$', views.retrieve, name='retrieve'),
    url(r'^identical/$', views.identical, name="identical"),
    re_path(r'^', include(router.urls)),

    url(r'^login/$', login, {'template_name': 'admin/login.html'}, name="login"),
    re_path(r'^', include('django.contrib.auth.urls')),

]
