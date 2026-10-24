from pealang.kubernetes_security import SecureKubernetesConfig,write_secure_manifests
write_secure_manifests("k8s-secure",SecureKubernetesConfig(name="pealang-demo",image="registry.example.com/pealang-demo:0.61.0",service_account="pealang-model",config_map="pealang-config",secret_name="pealang-secrets"))
