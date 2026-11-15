from django.urls import path

from . import views

app_name = "contas"

urlpatterns = [
    path("entrar/", views.EntrarView.as_view(), name="entrar"),
    path("sair/", views.SairView.as_view(), name="sair"),
    path("criar/", views.criar_conta, name="criar"),
    path("minha-conta/", views.minha_conta, name="minha_conta"),
    path("senha/esqueci/", views.EsqueciSenhaView.as_view(), name="senha_esqueci"),
    path("senha/enviada/", views.SenhaEnviadaView.as_view(), name="senha_enviada"),
    path("senha/nova/<uidb64>/<token>/", views.NovaSenhaView.as_view(), name="senha_nova"),
    path("senha/concluida/", views.SenhaConcluidaView.as_view(), name="senha_concluida"),
]