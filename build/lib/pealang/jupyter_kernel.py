


"""Optional ipykernel adapter. Core protocol remains usable without Jupyter installed."""
from .jupyter import PeaKernel,kernelspec

def main():
    try:
        from ipykernel.kernelbase import Kernel
        from ipykernel.kernelapp import IPKernelApp
    except ImportError as exc:
        raise SystemExit("Install ipykernel to launch the PeaLang Jupyter kernel") from exc
    class KernelAdapter(Kernel):
        implementation="pealang"; implementation_version="0.72.0"; language="pealang"; language_info=PeaKernel.language_info; banner="PeaLang 0.72"
        def __init__(self,*a,**kw): super().__init__(*a,**kw); self.runtime=PeaKernel()
        def do_execute(self,code,silent,store_history=True,user_expressions=None,allow_stdin=False):
            r=self.runtime.execute(code,silent); return {k:v for k,v in r.items() if k not in {"display_data","metadata"}}
    IPKernelApp.launch_instance(kernel_class=KernelAdapter)
if __name__=="__main__": main()



