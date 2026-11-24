from django.urls import path

from . import views

app_name = "site_publico"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("orientacoes/", views.orientacoes, name="orientacoes"),
    path("profissionais/<int:pk>/", views.profissional, name="profissional"),
    path("privacidade/", views.privacidade, name="privacidade"),
    path("termos-de-uso/", views.termos, name="termos"),
    path("orientacoes/<slug:slug>/", views.orientacao, name="orientacao"),
]
