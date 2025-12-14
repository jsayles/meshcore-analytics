from rest_framework.routers import DefaultRouter
from .views import NodeViewSet, FieldTestViewSet, TraceViewSet

router = DefaultRouter()
router.register(r"nodes", NodeViewSet, basename="node")
router.register(r"field-tests", FieldTestViewSet, basename="field-test")
router.register(r"traces", TraceViewSet, basename="trace")

urlpatterns = router.urls
