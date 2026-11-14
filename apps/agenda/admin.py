from django.contrib import admin

from apps.clinica.admin import ProfissionalAdmin
from apps.clinica.models import Profissional

from .models import Bloqueio, HorarioAtendimento


@admin.register(HorarioAtendimento)
class HorarioAtendimentoAdmin(admin.ModelAdmin):
    list_display = ["profissional", "dia_semana", "hora_inicio", "hora_fim", "intervalo_inicio", "intervalo_fim", "ativo"]
    list_filter = ["profissional", "dia_semana", "ativo"]


@admin.register(Bloqueio)
class BloqueioAdmin(admin.ModelAdmin):
    list_display = ["motivo", "profissional", "inicio", "fim"]
    list_filter = ["profissional"]
    search_fields = ["motivo"]
    date_hierarchy = "inicio"


class HorarioAtendimentoInline(admin.TabularInline):
    model = HorarioAtendimento
    extra = 0
    fields = ["dia_semana", "hora_inicio", "hora_fim", "intervalo_inicio", "intervalo_fim", "ativo"]


# Mostra os horários dentro da tela do profissional.
admin.site.unregister(Profissional)


@admin.register(Profissional)
class ProfissionalComHorariosAdmin(ProfissionalAdmin):
    inlines = [HorarioAtendimentoInline]
