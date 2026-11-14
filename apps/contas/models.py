from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UsuarioManager(BaseUserManager):
    """Cria usuários usando o e-mail como login."""

    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("tipo", Usuario.Tipo.ADMIN)
        if extra.get("is_staff") is not True or extra.get("is_superuser") is not True:
            raise ValueError("O superusuário precisa de is_staff=True e is_superuser=True.")
        return self.create_user(email, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    class Tipo(models.TextChoices):
        PACIENTE = "paciente", "Paciente"
        RECEPCAO = "recepcao", "Recepção"
        PROFISSIONAL = "profissional", "Profissional"
        ADMIN = "admin", "Administrador"

    email = models.EmailField("e-mail", unique=True)
    nome = models.CharField("nome", max_length=150)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    tipo = models.CharField("tipo", max_length=20, choices=Tipo.choices, default=Tipo.PACIENTE)
    is_active = models.BooleanField("ativo", default=True)
    is_staff = models.BooleanField("acesso ao admin", default=False)
    criado_em = models.DateTimeField("criado em", auto_now_add=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nome"]

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} <{self.email}>"
