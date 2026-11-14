from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.core.models import ModeloBase


class Especialidade(ModeloBase):
    nome = models.CharField("nome", max_length=100, unique=True)
    slug = models.SlugField("slug", max_length=110, unique=True, blank=True)
    descricao = models.TextField("descrição", blank=True)

    class Meta:
        verbose_name = "especialidade"
        verbose_name_plural = "especialidades"
        ordering = ["nome"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome


class Servico(ModeloBase):
    especialidade = models.ForeignKey(
        Especialidade,
        on_delete=models.PROTECT,
        related_name="servicos",
        verbose_name="especialidade",
    )
    nome = models.CharField("nome", max_length=120)
    descricao = models.TextField("descrição", blank=True)
    duracao_min = models.PositiveSmallIntegerField("duração (minutos)", default=30)
    preco = models.DecimalField("preço (R$)", max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = "serviço"
        verbose_name_plural = "serviços"
        ordering = ["especialidade__nome", "nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["especialidade", "nome"], name="servico_unico_por_especialidade"
            ),
        ]

    def __str__(self):
        return f"{self.nome} ({self.duracao_min} min)"


class Profissional(ModeloBase):
    class Conselho(models.TextChoices):
        CRM = "CRM", "CRM (medicina)"
        CRO = "CRO", "CRO (odontologia)"
        OUTRO = "OUTRO", "Outro"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="profissional",
        verbose_name="usuário",
    )
    conselho = models.CharField("conselho", max_length=10, choices=Conselho.choices, default=Conselho.CRM)
    registro = models.CharField("número do registro", max_length=20)
    uf_registro = models.CharField("UF do registro", max_length=2, default="PI")
    foto = models.ImageField("foto", upload_to="profissionais/", blank=True)
    bio = models.TextField("apresentação", blank=True)
    especialidades = models.ManyToManyField(
        Especialidade, related_name="profissionais", verbose_name="especialidades"
    )
    servicos = models.ManyToManyField(
        Servico, related_name="profissionais", verbose_name="serviços", blank=True
    )

    class Meta:
        verbose_name = "profissional"
        verbose_name_plural = "profissionais"
        ordering = ["usuario__nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["conselho", "registro", "uf_registro"], name="registro_profissional_unico"
            ),
        ]

    @property
    def nome(self):
        return self.usuario.nome

    @property
    def registro_formatado(self):
        return f"{self.conselho} {self.registro}/{self.uf_registro}"

    def __str__(self):
        return f"{self.nome} – {self.registro_formatado}"
