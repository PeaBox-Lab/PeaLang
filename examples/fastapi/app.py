


from pathlib import Path
from fastapi import FastAPI
from pealang import RuntimeOptions,VMRuntime
from pealang.fastapi import PeaExtensionRegistry,PeaRouter,install_exception_handlers
base=Path(__file__).parent
runtime=VMRuntime(RuntimeOptions(max_execution_ms=500,max_instructions=50000))
registry=PeaExtensionRegistry(runtime,hot_reload=True)
registry.load('hr',base/'rules.pea')
pea=PeaRouter(registry,prefix='/api').add('/bonus','hr','bonus').include_status()
app=FastAPI(title='PeaLang FastAPI Example')
app.include_router(pea.router)
install_exception_handlers(app)



