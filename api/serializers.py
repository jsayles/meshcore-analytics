from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework import serializers
from metro.models import Node, FieldTest, Trace, Role, HotspotConfig
from metro.subsystems import wifi_hotspot


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


class HotspotConfigSerializer(serializers.ModelSerializer):
    """
    Serializer for HotspotConfig model.
    Password is write-only for security.
    """

    ssid = serializers.CharField(min_length=1, max_length=32, required=False, help_text="WiFi SSID (1-32 characters)")
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
        min_length=8,
        max_length=63,
        help_text="WiFi password (8-63 characters for WPA/WPA2)",
    )
    connection_status = serializers.SerializerMethodField()

    class Meta:
        model = HotspotConfig
        fields = ["id", "ssid", "password", "connection_status"]
        read_only_fields = ["id", "connection_status"]

    def validate_ssid(self, value):
        """Validate SSID contains only printable characters."""
        if not value.isprintable():
            raise serializers.ValidationError("SSID must contain only printable characters")
        return value

    def validate_password(self, value):
        """Validate password meets WPA2-PSK requirements."""
        if not value.isprintable():
            raise serializers.ValidationError("Password must contain only printable characters")
        return value

    def get_connection_status(self, _obj):
        try:
            wifi_manager = wifi_hotspot.get_wifi_manager()
            return wifi_manager.check_status()
        except wifi_hotspot.UnsupportedPlatformError:
            return {
                "connected": False,
                "ssid": None,
                "error": "Platform not supported",
                "platform_support": False,
                "last_check": None,
            }

    def create(self, validated_data):
        instance = HotspotConfig.get_instance()
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
