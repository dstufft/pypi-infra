import invoke
import kubernetes as k8s

from . import vault

k8s.config.load_kube_config()

ns = invoke.Collection(vault)
ns.configure({"run": {"echo": True}})
