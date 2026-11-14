from django.urls import path

from . import views

app_name = "site_publico"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("orientacoes/", views.orientacoes, name="orientacoes"),
    path("orientacoes/<slug:slug>/", views.orientacao, name="orientacao"),
]
