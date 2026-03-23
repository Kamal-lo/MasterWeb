# core/urls.py
from django.urls import path
from . import views
from . import admin_views

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

    # Admin routes
    path('gestion/login/', admin_views.admin_login, name='admin_login'),
    path('gestion/logout/', admin_views.admin_logout, name='admin_logout'),
    path('gestion/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('gestion/etudiants/', admin_views.admin_students, name='admin_students'),
    path('gestion/notes/', admin_views.admin_grades, name='admin_grades'),
    path('gestion/modules/', admin_views.admin_modules, name='admin_modules'),
    path('gestion/professeurs/', admin_views.admin_professors, name='admin_professors'),
    path('gestion/comptes/', admin_views.admin_accounts, name='admin_accounts'),
]

