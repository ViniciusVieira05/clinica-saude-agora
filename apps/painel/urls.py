from django.urls import path

from . import views

app_name = "painel"

urlpatterns = [
    path("", views.agenda, name="agenda"),
    path("consulta/<int:pk>/pagamento/", views.pagamento, name="pagamento"),
    path("consulta/<int:pk>/<str:nome>/", views.acao, name="acao"),
    path("nova-consulta/", views.nova_consulta, name="nova_consulta"),
    path("pacientes/", views.pacientes, name="pacientes"),
    path("pacientes/buscar/", views.buscar_pacientes, name="buscar_pacientes"),
    path("pacientes/novo/", views.paciente_form, name="paciente_novo"),
    path("pacientes/<int:pk>/", views.paciente_detalhe, name="paciente"),
    path("pacientes/<int:pk>/editar/", views.paciente_form, name="paciente_editar"),
]
