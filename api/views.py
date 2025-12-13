from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.gis.geos import Point
from django.utils import timezone
from asgiref.sync import async_to_sync
import asyncio

from metro.models import Node, MappingSession, Trace, Role
from metro.radio_interface import RadioInterface
from .serializers import NodeSerializer, MappingSessionSerializer, TraceSerializer


class NodeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Nodes.
    Supports CRUD operations plus discovery endpoint.
    """

    queryset = Node.objects.all().order_by("name")
    serializer_class = NodeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "role"]
    search_fields = ["name", "mesh_identity"]
    ordering_fields = ["name", "last_seen"]

    @action(detail=False, methods=["post"])
    def discover(self, request):
        """
        Discover all repeaters from radio, excluding ones already in database.
        Returns transient discovery results (not saved to database).
        """
        try:
            # Run discovery in async context
            async def run_discovery():
                radio = RadioInterface()
                await radio.connect()
                try:
                    timeout = request.data.get("timeout", 30)
                    discovered = await radio.discover_nodes(timeout=timeout)
                    return discovered
                finally:
                    await radio.disconnect()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                discovered_nodes = loop.run_until_complete(run_discovery())
            finally:
                loop.close()

            # Filter out nodes already in database
            existing_mesh_ids = set(Node.objects.filter(role=Role.REPEATER).values_list("mesh_identity", flat=True))
            filtered_nodes = [node for node in discovered_nodes if node["mesh_identity"] not in existing_mesh_ids]

            return Response({"count": len(filtered_nodes), "nodes": filtered_nodes})

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def add_node(self, request):
        """
        Add a discovered node to the database.
        Expects discovery data in request body.
        """
        try:
            data = request.data

            # Check if node already exists
            mesh_identity = data.get("mesh_identity")
            if Node.objects.filter(mesh_identity=mesh_identity).exists():
                return Response({"error": "Node already exists"}, status=status.HTTP_400_BAD_REQUEST)

            # Create node from discovery data
            node = Node.objects.create(
                mesh_identity=mesh_identity,
                public_key=data.get("pubkey", ""),
                name=data.get("name", ""),
                role=Role.CLIENT if data.get("node_type") == 1 else Role.REPEATER,
                last_seen=timezone.now(),
            )

            # Add location if provided
            lat = data.get("lat")
            lon = data.get("lon")
            if lat and lon:
                node.location = Point(lon, lat, srid=4326)
                node.save()

            serializer = self.get_serializer(node)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MappingSessionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for mapping sessions.
    Supports creating, updating, and retrieving mapping sessions.
    """

    queryset = MappingSession.objects.all().select_related("target_node")
    serializer_class = MappingSessionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["target_node", "end_time"]
    ordering_fields = ["start_time"]
    ordering = ["-start_time"]


class TraceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for trace measurements.
    Supports creating new traces and retrieving for heatmap display.
    """

    queryset = Trace.objects.all().select_related("session__target_node")
    serializer_class = TraceSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["session", "session__target_node"]
    ordering_fields = ["timestamp"]
    ordering = ["-timestamp"]
