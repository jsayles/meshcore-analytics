from django.shortcuts import render, get_object_or_404, redirect
import uuid
from .models import Node, Role


def mesh_home(request):
    """Render the network overview map showing all nodes"""
    # Redirect to config if no repeaters in database
    if Node.objects.filter(role=Role.REPEATER).count() == 0:
        return redirect("config_mesh")
    return render(request, "metro/mesh_home.html")


def config_redirect(request):
    """Redirect /config/ to /config/mesh/"""
    return redirect("config_mesh")


def config_mesh(request):
    """Mesh configuration page - repeaters management"""
    return render(request, "metro/config_mesh.html")


def config_hotspot(request):
    """Hotspot configuration page - WiFi management"""
    return render(request, "metro/config_hotspot.html")


def node_detail(request, node_id):
    """Render detailed view of a specific node"""
    node = get_object_or_404(Node, id=node_id)
    return render(request, "metro/node_detail.html", {"node": node})


def field_testing(request):
    """Render the field testing interface"""
    # Field tests are now created explicitly via API when user starts testing
    return render(request, "metro/field_testing.html")
