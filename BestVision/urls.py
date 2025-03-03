from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('child/add/', views.ChildCreateView.as_view(), name='add_child'),
    path('donation/<int:pk>/', views.update_donation, name='update_donation'),
    path('optimize/', views.optimize_resources, name='optimize_resources'),
    path('allocations/', views.allocation_list, name='allocation_list'),
]

