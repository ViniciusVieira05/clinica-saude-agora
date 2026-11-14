from django.conf import settings
from django.db import models


class ModeloBase(models.Model):
    """Campos que todos os models do sistema têm."""

    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        abstract = True


class LogAuditoria(models.Model):
    """Registro de quem criou, alterou ou excluiu cada cadastro (RNF04 / LGPD)."""

    class Acao(models.TextChoices):
        CRIAR = "criar", "Criou"
        ALTERAR = "alterar", "Alterou"
        EXCLUIR = "excluir", "Excluiu"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
        verbose_name="usuário",
    )
    acao = models.CharField("ação", max_length=10, choices=Acao.choices)
    modelo = models.CharField("cadastro", max_length=100)
    objeto_id = models.CharField("ID do registro", max_length=50)
    descricao = models.CharField("descrição", max_length=255)
    dados_antes = models.JSONField("dados antes", null=True, blank=True)
    dados_depois = models.JSONField("dados depois", null=True, blank=True)
    ip = models.GenericIPAddressField("IP", null=True, blank=True)
    criado_em = models.DateTimeField("quando", auto_now_add=True)

    class Meta:
        verbose_name = "log de auditoria"
        verbose_name_plural = "logs de auditoria"
        ordering = ["-criado_em"]
        indexes = [models.Index(fields=["modelo", "objeto_id"])]

    def __str__(self):
        quem = self.usuario.nome if self.usuario else "Sistema"
        return f"{quem} {self.get_acao_display().lower()} {self.modelo} #{self.objeto_id}"
