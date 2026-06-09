from kmap.kubernetes.client import KubectlClient as ClientImpl
from kmap.kubernetes.network import service_entrypoints as service_entrypoints_impl
from kmap.kubernetes.objects import obj_name as obj_name_impl


def test_kubernetes_owning_modules_export_public_helpers():
    assert ClientImpl
    assert obj_name_impl({"metadata": {"name": "demo"}}) == "demo"
    assert service_entrypoints_impl({"metadata": {"name": "api"}, "spec": {}}, "default")
