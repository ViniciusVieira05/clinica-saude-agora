from django.contrib import admin

from .models import Atendimento


@admin.register(Atendimento)
class AtendimentoAdmin(admin.ModelAdmin):
    list_display = ["consulta", "realizado_em", "retorno_sugerido_em", "registrado_por"]
    search_fields = ["consulta__paciente__nome"]
    date_hierarchy = "realizado_em"
    raw_id_fields = ["consulta"]
    readonly_fields = ["registrado_por", "criado_em", "atualizado_em"]
