from django import forms

from apps.core.validators import somente_digitos
from apps.pacientes.models import Paciente


class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ["nome", "cpf", "data_nascimento", "sexo", "telefone", "email",
                  "cep", "endereco", "bairro", "cidade", "uf", "observacoes"]
        widgets = {
            "data_nascimento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "cpf": forms.TextInput(attrs={"inputmode": "numeric", "placeholder": "000.000.000-00", "data-mascara": "cpf"}),
            "telefone": forms.TextInput(attrs={"inputmode": "tel", "placeholder": "(00) 00000-0000", "data-mascara": "telefone"}),
            "cep": forms.TextInput(attrs={"inputmode": "numeric", "data-mascara": "cep", "data-viacep": "1", "placeholder": "00000-000"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_cpf(self):
        cpf = somente_digitos(self.cleaned_data["cpf"])
        existe = Paciente.objects.filter(cpf=cpf).exclude(pk=self.instance.pk)
        if existe.exists():
            raise forms.ValidationError("Já existe um paciente com este CPF.")
        return cpf
