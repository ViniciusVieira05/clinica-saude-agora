from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ["nome"]
    list_display = ["nome", "email", "tipo", "is_active"]
    list_filter = ["tipo", "is_active", "is_staff"]
    search_fields = ["nome", "email"]
    readonly_fields = ["last_login", "criado_em"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Dados pessoais", {"fields": ("nome", "telefone", "tipo")}),
        ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Datas", {"fields": ("last_login", "criado_em")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "nome", "tipo", "password1", "password2"),
        }),
    )
