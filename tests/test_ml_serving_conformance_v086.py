


from pealang.ml_serving_conformance import *
def test_v86():
 c=ModelContract(ModelFormat.ONNX,{},{});assert ModelCompatibilityMatrix().register("m",c).supports("m","onnx");assert DeterministicInferenceSuite().run(lambda x:[2],c,[InferenceFixture("a",{},[2])])[0]["status"]=="PASS"



