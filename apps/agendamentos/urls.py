from django.urls import path

from . import views

app_name = "agendamentos"

urlpatterns = [
    path("", views.agendar, name="agendar"),
    path("confirmar/", views.confirmar, name="confirmar"),
    path("confirmado/<int:pk>/", views.confirmado, name="confirmado"),
    path("meus/", views.meus_agendamentos, name="meus"),
    path("meus/<int:pk>/cancelar/", views.cancelar, name="cancelar"),
    path("meus/<int:pk>/remarcar/", views.remarcar, name="remarcar"),
]
