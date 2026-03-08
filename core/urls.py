# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('demande_recorrection/', views.demande_rec, name='demande'),
    path('reponse_demande/', views.reponse_demande, name='reponse'),
    path('actuelle/', views.actuelle,name='actuelle'),
    path('group/', views.group, name='group'),
    path('emplois_temps/', views.emplois_temps, name='emp'),
    path('information_scolaire/', views.information_scolaire, name='information_scolaire'),
    path('information_prive/', views.information_prive, name='information_prive'),
    path('resultat/', views.resultat, name='resultat'),
]
