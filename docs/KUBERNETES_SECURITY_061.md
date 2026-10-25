

# Kubernetes Security and RC Stabilization 0.61

Adds YAML rendering, non-root pod/container security contexts, read-only root filesystems, seccomp RuntimeDefault, all Linux capabilities dropped, temporary emptyDir storage, network policies, PodDisruptionBudget, topology spread, anti-affinity, graceful drain control, manifest validation, release-candidate compatibility matrix and soak testing. Generated NetworkPolicy egress is a secure starting point and must be adapted to actual Redis, telemetry and registry endpoints.


