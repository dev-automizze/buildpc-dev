from django.urls import path

from . import views

urlpatterns = [
    path("api/cpus/", views.get_cpus, name="get_cpus"),
    path("api/motherboards/", views.get_motherboards, name="get_motherboards"),
    path("api/coolers/", views.get_coolers, name="get_coolers"),
    path("api/ram/", views.get_ram, name="get_ram"),
    path("api/sockets/", views.get_sockets, name="get_sockets"),
]
