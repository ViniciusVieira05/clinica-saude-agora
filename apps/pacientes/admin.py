from django.contrib import admin

from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ["nome", "cpf_formatado", "telefone", "data_nascimento", "ativo"]
    list_filter = ["ativo", "sexo", "cidade"]
    search_fields = ["nome", "cpf", "telefone", "email"]
    autocomplete_fields = ["usuario"]
    readonly_fields = ["aceite_termos_em", "criado_em", "atualizado_em"]
    fieldsets = (
        ("Identificação", {"fields": ("nome", "cpf", "data_nascimento", "sexo", "usuario")}),
        ("Contato", {"fields": ("telefone", "email")}),
        ("Endereço", {"fields": ("cep", "endereco", "bairro", "cidade", "uf")}),
        ("Outros", {"fields": ("observacoes", "ativo", "aceite_termos_em", "criado_em", "atualizado_em")}),
    )

    @admin.display(description="CPF", ordering="cpf")
    def cpf_formatado(self, obj):
        return obj.cpf_formatado
