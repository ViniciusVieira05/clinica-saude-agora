from django.contrib import admin

from .models import LogAuditoria


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    """Somente leitura: ninguém edita ou apaga o histórico."""

    list_display = ["criado_em", "usuario", "acao", "modelo", "descricao"]
    list_filter = ["acao", "modelo"]
    search_fields = ["descricao", "objeto_id", "usuario__nome"]
    date_hierarchy = "criado_em"
    readonly_fields = [f.name for f in LogAuditoria._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
