from django.contrib import admin
from django.utils.html import format_html

from .models import Avaliacao, Convenio, FotoClinica, Orientacao, PerguntaFrequente


class MiniaturaMixin:
    campo_imagem = "imagem"

    @admin.display(description="prévia")
    def previa(self, obj):
        imagem = getattr(obj, self.campo_imagem)
        if imagem:
            return format_html('<img src="{}" style="height:48px;border-radius:6px">', imagem.url)
        return "—"


@admin.register(Convenio)
class ConvenioAdmin(MiniaturaMixin, admin.ModelAdmin):
    campo_imagem = "logo"
    list_display = ["nome", "previa", "ordem", "ativo"]
    list_editable = ["ordem", "ativo"]


@admin.register(FotoClinica)
class FotoClinicaAdmin(MiniaturaMixin, admin.ModelAdmin):
    list_display = ["legenda", "previa", "ordem", "ativo"]
    list_editable = ["ordem", "ativo"]


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ["autor", "nota", "data", "ordem", "ativo"]
    list_editable = ["ordem", "ativo"]
    search_fields = ["autor", "texto"]


@admin.register(PerguntaFrequente)
class PerguntaFrequenteAdmin(admin.ModelAdmin):
    list_display = ["pergunta", "ordem", "ativo"]
    list_editable = ["ordem", "ativo"]


@admin.register(Orientacao)
class OrientacaoAdmin(MiniaturaMixin, admin.ModelAdmin):
    list_display = ["titulo", "previa", "publicado_em", "ativo"]
    list_filter = ["ativo"]
    search_fields = ["titulo", "resumo"]
    prepopulated_fields = {"slug": ["titulo"]}
