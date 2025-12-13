from django.shortcuts import render, get_object_or_404, redirect
import uuid
from .models import Node, Role


def mesh_home(request):
    """Render the network overview map showing all nodes"""
    # Redirect to config if no repeaters in database
    if Node.objects.filter(role=Role.REPEATER).count() == 0:
        return redirect("mesh_config")
    return render(request, "metro/mesh_home.html")


def mesh_config(request):
    """Render the mesh configuration interface"""
    return render(request, "metro/mesh_config.html")


def node_detail(request, node_id):
    """Render detailed view of a specific node"""
    node = get_object_or_404(Node, id=node_id)
    return render(request, "metro/node_detail.html", {"node": node})


def signal_mapper(request):
    """Render the signal mapping interface"""
    # Sessions are now created explicitly via API when user starts mapping
    return render(request, "metro/signal_mapper.html")
