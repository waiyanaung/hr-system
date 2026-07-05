from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("employees/new/", views.create_employee, name="create_employee"),
    path("employees/<str:emp_id>/delete/", views.delete_employee, name="delete_employee"),
]