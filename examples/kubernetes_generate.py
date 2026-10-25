
from pealang.distributed_serving import KubernetesConfig,write_kubernetes_manifests
write_kubernetes_manifests("k8s",KubernetesConfig(name="pealang-demo",image="registry.example.com/pealang-demo:0.60.0",config_map="pealang-config",secret_name="pealang-secrets"))

