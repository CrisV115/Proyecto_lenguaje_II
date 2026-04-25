from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("users.urls")),
    path("tests/", include("tests_academic.urls")),
    path("courses/", include("courses.urls")),
    path("tracking/", include("tracking.urls")),
    path("certifications/", include("certifications.urls")),
    path("leveling/", include("leveling.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
