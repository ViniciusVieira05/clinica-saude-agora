from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from apps.core.models import ModeloBase


class Ordenavel(ModeloBase):
    ordem = models.PositiveSmallIntegerField("ordem", default=0, help_text="Menor número aparece primeiro.")

    class Meta:
        abstract = True
        ordering = ["ordem", "id"]


class Convenio(Ordenavel):
    nome = models.CharField("nome", max_length=100)
    logo = models.ImageField("logo", upload_to="convenios/", blank=True)

    class Meta(Ordenavel.Meta):
        verbose_name = "convênio"
        verbose_name_plural = "convênios"

    def __str__(self):
        return self.nome


class FotoClinica(Ordenavel):
    imagem = models.ImageField("foto", upload_to="clinica/")
    legenda = models.CharField("legenda", max_length=80, help_text="Ex.: Recepção, Consultório 1, Sala de exames.")

    class Meta(Ordenavel.Meta):
        verbose_name = "foto da clínica"
        verbose_name_plural = "fotos da clínica"

    def __str__(self):
        return self.legenda


class Avaliacao(Ordenavel):
    """Avaliações REAIS copiadas do Google, sempre com o link da original."""

    autor = models.CharField("nome de quem avaliou", max_length=100)
    texto = models.TextField("texto da avaliação", max_length=600)
    nota = models.PositiveSmallIntegerField("nota (1 a 5)", default=5, choices=[(i, i) for i in range(1, 6)])
    link = models.URLField("link da avaliação no Google", help_text="Cole o link da avaliação original.")
    data = models.DateField("data da avaliação", null=True, blank=True)

    class Meta(Ordenavel.Meta):
        verbose_name = "avaliação do Google"
        verbose_name_plural = "avaliações do Google"

    def __str__(self):
        return f"{self.autor} ({self.nota}★)"


class PerguntaFrequente(Ordenavel):
    pergunta = models.CharField("pergunta", max_length=200)
    resposta = models.TextField("resposta")

    class Meta(Ordenavel.Meta):
        verbose_name = "pergunta frequente"
        verbose_name_plural = "perguntas frequentes"

    def __str__(self):
        return self.pergunta


class Orientacao(ModeloBase):
    titulo = models.CharField("título", max_length=150)
    slug = models.SlugField("endereço (slug)", max_length=160, unique=True, blank=True)
    resumo = models.CharField("resumo", max_length=220)
    conteudo = models.TextField("conteúdo", help_text="Texto simples. Deixe uma linha em branco entre os parágrafos.")
    imagem = models.ImageField("imagem de capa", upload_to="orientacoes/", blank=True)
    publicado_em = models.DateField("publicado em", default=timezone.localdate)

    class Meta:
        verbose_name = "orientação"
        verbose_name_plural = "orientações"
        ordering = ["-publicado_em", "-id"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)[:160]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("site_publico:orientacao", args=[self.slug])

    def __str__(self):
        return self.titulo
