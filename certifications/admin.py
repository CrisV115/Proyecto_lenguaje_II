from django.contrib import admin

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("student", "code", "source_phase", "valid", "issue_date")
    list_filter = ("valid", "source_phase")
    search_fields = ("student__username", "code")
