from django.contrib import admin

from .models import Pagamento


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ["pago_em", "consulta", "valor", "forma", "registrado_por"]
    list_filter = ["forma", "ativo"]
    search_fields = ["consulta__paciente__nome"]
    date_hierarchy = "pago_em"
    raw_id_fields = ["consulta"]
    readonly_fields = ["registrado_por", "criado_em", "atualizado_em"]

    def save_model(self, request, obj, form, change):
        if not obj.registrado_por:
            obj.registrado_por = request.user
        super().save_model(request, obj, form, change)
