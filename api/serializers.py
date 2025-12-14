from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework import serializers
from metro.models import Node, FieldTest, Trace, Role


class NodeSerializer(GeoFeatureModelSerializer):
    """
    Serializer for Node model with GeoJSON support.
    Used for listing repeaters available for testing.
    """

    class Meta:
        model = Node
        geo_field = "location"
        fields = ["id", "name", "mesh_identity", "role", "is_active", "last_seen", "location", "estimated_range"]


class FieldTestSerializer(serializers.ModelSerializer):
    """
    Serializer for FieldTest model.
    Handles explicit field tests with start/end times.
    """

    is_active = serializers.ReadOnlyField()
    duration = serializers.ReadOnlyField()

    class Meta:
        model = FieldTest
        fields = [
            "id",
            "target_node",
            "start_time",
            "end_time",
            "notes",
            "is_active",
            "duration",
        ]
        read_only_fields = ["id", "start_time", "is_active", "duration"]


class TraceSerializer(GeoFeatureModelSerializer):
    """
    Serializer for Trace model with GeoJSON support.
    Handles individual signal trace measurements during a field test.
    """

    target_node = serializers.ReadOnlyField(source="field_test.target_node.id")

    class Meta:
        model = Trace
        geo_field = "location"
        fields = [
            "id",
            "field_test",
            "location",
            "altitude",
            "gps_accuracy",
            "target_node",
            "snr_to_target",
            "snr_from_target",
            "trace_success",
            "timestamp",
        ]
        read_only_fields = ["id", "timestamp", "target_node"]
