from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Saúde Agora · Administração"
admin.site.site_title = "Saúde Agora"
admin.site.index_title = "Painel administrativo"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("conta/", include("apps.contas.urls")),
    path("agendar/", include("apps.agendamentos.urls")),
    path("painel/", include("apps.painel.urls")),
    path("", include("apps.site_publico.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
