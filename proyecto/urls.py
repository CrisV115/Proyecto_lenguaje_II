from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("users.urls")),
    path("tests/", include("tests_academic.urls")),
    path("tracking/", include("tracking.urls")),
    path("certifications/", include("certifications.urls")),
    path("leveling/", include("leveling.urls")),
]
