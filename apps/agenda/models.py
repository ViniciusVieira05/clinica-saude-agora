from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from apps.clinica.models import Profissional
from apps.core.models import ModeloBase


class HorarioAtendimento(ModeloBase):
    """Expediente semanal de um profissional (ex.: segunda, 08:00 às 17:00, intervalo 12:00 às 13:00)."""

    class DiaSemana(models.IntegerChoices):
        SEGUNDA = 0, "Segunda-feira"
        TERCA = 1, "Terça-feira"
        QUARTA = 2, "Quarta-feira"
        QUINTA = 3, "Quinta-feira"
        SEXTA = 4, "Sexta-feira"
        SABADO = 5, "Sábado"
        DOMINGO = 6, "Domingo"

    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        related_name="horarios",
        verbose_name="profissional",
    )
    dia_semana = models.PositiveSmallIntegerField("dia da semana", choices=DiaSemana.choices)
    hora_inicio = models.TimeField("início")
    hora_fim = models.TimeField("fim")
    intervalo_inicio = models.TimeField("início do intervalo", null=True, blank=True)
    intervalo_fim = models.TimeField("fim do intervalo", null=True, blank=True)

    class Meta:
        verbose_name = "horário de atendimento"
        verbose_name_plural = "horários de atendimento"
        ordering = ["profissional", "dia_semana", "hora_inicio"]
        constraints = [
            models.UniqueConstraint(
                fields=["profissional", "dia_semana"], name="um_horario_por_dia_por_profissional"
            ),
            models.CheckConstraint(
                condition=Q(hora_inicio__lt=F("hora_fim")), name="horario_inicio_antes_do_fim"
            ),
        ]

    def clean(self):
        if self.hora_inicio and self.hora_fim and self.hora_inicio >= self.hora_fim:
            raise ValidationError("O início precisa ser antes do fim.")
        tem_inicio = self.intervalo_inicio is not None
        tem_fim = self.intervalo_fim is not None
        if tem_inicio != tem_fim:
            raise ValidationError("Preencha início e fim do intervalo, ou deixe os dois vazios.")
        if tem_inicio and tem_fim:
            if not (self.hora_inicio < self.intervalo_inicio < self.intervalo_fim < self.hora_fim):
                raise ValidationError("O intervalo precisa ficar dentro do expediente.")

    def __str__(self):
        return f"{self.profissional.nome} – {self.get_dia_semana_display()} {self.hora_inicio:%H:%M}–{self.hora_fim:%H:%M}"


class Bloqueio(ModeloBase):
    """Período sem atendimento: folga, férias, congresso ou feriado.
    Sem profissional = bloqueio da clínica inteira (ex.: feriado)."""

    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="bloqueios",
        verbose_name="profissional",
        help_text="Deixe vazio para bloquear a clínica inteira.",
    )
    inicio = models.DateTimeField("início")
    fim = models.DateTimeField("fim")
    motivo = models.CharField("motivo", max_length=150)

    class Meta:
        verbose_name = "bloqueio"
        verbose_name_plural = "bloqueios"
        ordering = ["-inicio"]
        constraints = [
            models.CheckConstraint(
                condition=Q(inicio__lt=F("fim")), name="bloqueio_inicio_antes_do_fim"
            ),
        ]
        indexes = [models.Index(fields=["profissional", "inicio", "fim"])]

    def clean(self):
        if self.inicio and self.fim and self.inicio >= self.fim:
            raise ValidationError("O início precisa ser antes do fim.")

    def __str__(self):
        quem = self.profissional.nome if self.profissional else "Clínica inteira"
        return f"{quem}: {self.motivo} ({self.inicio:%d/%m/%Y})"
