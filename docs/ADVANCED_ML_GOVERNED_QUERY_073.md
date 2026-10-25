# PeaLang v0.73 Advanced ML and Governed Query Planning

v0.73 combines three roadmap targets: ONNX Runtime inference, PyTorch/tensor-DataFrame interchange, and governed natural-language query planning.

## ONNX
`ONNXModel` lazily loads `onnxruntime`, exposes model input metadata, accepts named tensors and can return predictions as a PeaLang `DataFrame`.

## Tensor interchange
`TensorBridge` converts DataFrames to dependency-free nested numeric arrays, converts tensors/NumPy arrays back to DataFrames, and optionally creates PyTorch tensors.

## Governed query planning
`GovernedQueryPlanner` is rule-first. A model may propose a structured plan, but `QueryPolicy` remains authoritative for allowed datasets, operations, limits, and approval requirements. The default planner does not execute queries.
