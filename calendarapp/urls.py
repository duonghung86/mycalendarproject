from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendar_view, name='calendar_view'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]