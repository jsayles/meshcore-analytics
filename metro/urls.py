from django.contrib import admin
from django.urls import path, include
from metro import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("api.urls")),
    path("", views.mesh_home, name="home"),
    path("config/", views.config_redirect, name="config"),
    path("config/mesh/", views.config_mesh, name="config_mesh"),
    path("config/hotspot/", views.config_hotspot, name="config_hotspot"),
    path("node/<int:node_id>/", views.node_detail, name="node_detail"),
    path("field-tests/", views.field_testing, name="field_test"),
]
