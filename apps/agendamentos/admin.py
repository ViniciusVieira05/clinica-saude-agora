from django.contrib import admin

from apps.atendimentos.models import Atendimento
from apps.financeiro.models import Pagamento

from .models import Consulta


class AtendimentoInline(admin.StackedInline):
    model = Atendimento
    extra = 0
    max_num = 1
    fields = ["observacoes", "retorno_sugerido_em", "realizado_em"]


class PagamentoInline(admin.TabularInline):
    model = Pagamento
    extra = 0
    fields = ["valor", "forma", "pago_em", "observacao"]


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ["inicio", "paciente", "profissional", "servico", "status", "origem", "encaixe"]
    list_filter = ["status", "profissional", "origem", "encaixe"]
    search_fields = ["paciente__nome", "paciente__cpf", "profissional__usuario__nome"]
    autocomplete_fields = ["paciente", "criado_por"]
    date_hierarchy = "inicio"
    readonly_fields = ["criado_em", "atualizado_em", "cancelada_em"]
    list_select_related = ["paciente", "profissional__usuario", "servico"]
    inlines = [AtendimentoInline, PagamentoInline]

    def save_model(self, request, obj, form, change):
        if not obj.criado_por:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        for item in formset.save(commit=False):
            if hasattr(item, "registrado_por") and not item.registrado_por:
                item.registrado_por = request.user
            item.save()
        for item in formset.deleted_objects:
            item.delete()
        formset.save_m2m()
