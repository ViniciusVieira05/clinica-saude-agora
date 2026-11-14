from django.contrib import admin

from .models import Especialidade, Profissional, Servico


class ServicoInline(admin.TabularInline):
    model = Servico
    extra = 1
    fields = ["nome", "duracao_min", "preco", "ativo"]


@admin.register(Especialidade)
class EspecialidadeAdmin(admin.ModelAdmin):
    list_display = ["nome", "ativo"]
    list_filter = ["ativo"]
    search_fields = ["nome"]
    prepopulated_fields = {"slug": ["nome"]}
    inlines = [ServicoInline]


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ["nome", "especialidade", "duracao_min", "preco", "ativo"]
    list_filter = ["especialidade", "ativo"]
    search_fields = ["nome"]
    list_editable = ["preco", "ativo"]


@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ["nome", "registro_formatado", "ativo"]
    list_filter = ["especialidades", "conselho", "ativo"]
    search_fields = ["usuario__nome", "registro"]
    autocomplete_fields = ["usuario"]
    filter_horizontal = ["especialidades", "servicos"]
