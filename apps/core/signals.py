"""Grava LogAuditoria sempre que um cadastro auditado é criado, alterado ou excluído."""
import json

from django.apps import apps
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.signals import post_delete, post_save, pre_save
from django.forms.models import model_to_dict

from .middleware import ip_atual, usuario_atual

MODELOS_AUDITADOS = [
    "pacientes.Paciente",
    "agendamentos.Consulta",
    "atendimentos.Atendimento",
    "financeiro.Pagamento",
    "clinica.Profissional",
    "clinica.Servico",
    "agenda.HorarioAtendimento",
    "agenda.Bloqueio",
]

CAMPOS_IGNORADOS = {"criado_em", "atualizado_em", "password"}


def _dados(instancia):
    campos = [f.name for f in instancia._meta.concrete_fields if f.name not in CAMPOS_IGNORADOS]
    dados = model_to_dict(instancia, fields=campos)
    return json.loads(json.dumps(dados, cls=DjangoJSONEncoder, default=str))


def _registrar(instancia, acao, antes, depois):
    LogAuditoria = apps.get_model("core", "LogAuditoria")
    LogAuditoria.objects.create(
        usuario=usuario_atual(),
        acao=acao,
        modelo=instancia._meta.verbose_name,
        objeto_id=str(instancia.pk),
        descricao=str(instancia)[:255],
        dados_antes=antes,
        dados_depois=depois,
        ip=ip_atual(),
    )


def _antes_de_salvar(sender, instance, **kwargs):
    instance._auditoria_antes = None
    if instance.pk:
        anterior = sender.objects.filter(pk=instance.pk).first()
        if anterior:
            instance._auditoria_antes = _dados(anterior)


def _depois_de_salvar(sender, instance, created, **kwargs):
    depois = _dados(instance)
    if created:
        _registrar(instance, "criar", None, depois)
        return
    antes = getattr(instance, "_auditoria_antes", None)
    if antes is not None:
        mudou = {k: v for k, v in depois.items() if antes.get(k) != v}
        if not mudou:
            return
        antes = {k: antes.get(k) for k in mudou}
        depois = mudou
    _registrar(instance, "alterar", antes, depois)


def _depois_de_excluir(sender, instance, **kwargs):
    _registrar(instance, "excluir", _dados(instance), None)


def conectar():
    for caminho in MODELOS_AUDITADOS:
        modelo = apps.get_model(caminho)
        uid = f"auditoria_{caminho}"
        pre_save.connect(_antes_de_salvar, sender=modelo, dispatch_uid=f"{uid}_pre")
        post_save.connect(_depois_de_salvar, sender=modelo, dispatch_uid=f"{uid}_post")
        post_delete.connect(_depois_de_excluir, sender=modelo, dispatch_uid=f"{uid}_del")
