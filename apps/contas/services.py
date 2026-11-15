"""Criação de conta do paciente."""
from django.db import transaction
from django.utils import timezone

from apps.pacientes.models import Paciente

from .models import Usuario


@transaction.atomic
def criar_conta_paciente(*, nome, cpf, data_nascimento, telefone, email, senha):
    """Cria o login e a ficha do paciente juntos.

    Se a recepção já tinha cadastrado esse CPF com a mesma data de nascimento
    (ficha sem login), liga a conta à ficha existente em vez de criar outra.
    """
    usuario = Usuario.objects.create_user(
        email=email, password=senha, nome=nome, telefone=telefone, tipo=Usuario.Tipo.PACIENTE
    )
    paciente = Paciente.objects.select_for_update().filter(
        cpf=cpf, data_nascimento=data_nascimento, usuario__isnull=True
    ).first()
    if paciente:
        # A ficha da recepção é a oficial: o nome do login passa a ser o da ficha.
        usuario.nome = paciente.nome
        usuario.save(update_fields=["nome"])
        paciente.usuario = usuario
        paciente.telefone = telefone
        paciente.email = email
        paciente.aceite_termos_em = timezone.now()
        paciente.save()
    else:
        Paciente.objects.create(
            usuario=usuario,
            nome=nome,
            cpf=cpf,
            data_nascimento=data_nascimento,
            telefone=telefone,
            email=email,
            aceite_termos_em=timezone.now(),
        )
    return usuario