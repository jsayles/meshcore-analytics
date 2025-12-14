from django.contrib import admin
from django.urls import path, include
from metro import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("api.urls")),
    path("", views.mesh_home, name="home"),
    path("config/", views.mesh_config, name="mesh_config"),
    path("node/<int:node_id>/", views.node_detail, name="node_detail"),
    path("field-testing/", views.field_testing, name="field_testing"),
]
