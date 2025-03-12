from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('child/add/', views.ChildCreateView.as_view(), name='add_child'),
    path('optimize/', views.optimize_resources, name='optimize_resources'),
    path('input/', views.resource_input, name='resource_input'),
]