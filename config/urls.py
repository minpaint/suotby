# config/urls.py — корневые маршруты
"""
Маршруты сайта.

⚠️ Порядок важен: служебные адреса идут первыми, последним — :class:`PageResolverView`,
который ищет материал или раздел по полному старому адресу.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path

from apps.content.views import PageResolverView, SearchView
from apps.core.views import HomeView
from apps.leads.views import LeadCreateView, LeadThanksView, lead_attachment
from apps.seo.sitemaps import SITEMAPS
from apps.seo.views import robots_txt

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("robots.txt", robots_txt, name="robots"),
    path(
        "sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="django.contrib.sitemaps.views.sitemap"
    ),
    path("poisk/", SearchView.as_view(), name="search"),
    path("zayavka/", LeadCreateView.as_view(), name="lead_create"),
    path("zayavka/spasibo/", LeadThanksView.as_view(), name="lead_thanks"),
    path(settings.ADMIN_URL + "leads/file/<int:pk>/", lead_attachment, name="lead_attachment"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
]

if settings.DEBUG:  # pragma: no cover — в проде медиа раздаёт Nginx
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [re_path(r"^(?P<path>.+)$", PageResolverView.as_view(), name="page")]

handler404 = "apps.core.views.page_not_found"
handler500 = "apps.core.views.server_error"
