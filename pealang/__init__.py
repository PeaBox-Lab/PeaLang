from .bytecode import BytecodeModule,CodeObject,Instruction,Op
from .compiler import Compiler,CompileError,compile_source_to_bytecode
from .vm import VirtualMachine,VMError,AsyncSuspension
from .async_vm import AsyncVirtualMachine,AsyncVMRuntime,AsyncVMModule,CancellationToken
from .vm_embedding import VMRuntime,VMModule
from .disassembler import disassemble
from .runtime import execute, compile_source, Interpreter, PeaError
from .type_system import TypeChecker,TypeRef,Diagnostic,TypeCheckResult,SemanticAnalyzer,SemanticResult,FunctionContract,parse_type,erase_types
from .embedding import (PeaRuntime,PeaModule,RuntimeOptions,ExecutionResult,
    PeaRuntimeError,PeaPermissionError,PeaResourceLimitError,to_pea,from_pea)
__version__='0.32.0'
__all__=['BytecodeModule','CodeObject','Instruction','Op','Compiler','CompileError','compile_source_to_bytecode','VirtualMachine','VMError','AsyncSuspension','AsyncVirtualMachine','AsyncVMRuntime','AsyncVMModule','CancellationToken','VMRuntime','VMModule','disassemble','execute','compile_source','Interpreter','PeaError','PeaRuntime','PeaModule',
'SemanticAnalyzer','SemanticResult','FunctionContract','TypeChecker','TypeRef','Diagnostic','TypeCheckResult','parse_type','erase_types','RuntimeOptions','ExecutionResult','PeaRuntimeError','PeaPermissionError',
'PeaResourceLimitError','to_pea','from_pea','__version__']

from .package_manager import Version,satisfies,load_pea_toml,init_manifest,resolve,write_lock,audit,build_package,install

from .runtime_service import RuntimeService,RuntimeResponse,ServiceError

from .browser_profile import BROWSER_SAFE_CAPABILITIES,validate_browser_permissions,validate_ui_schema

from .observability import Profiler,Coverage,Instrumentation,TraceEvent,Observer,MemoryObserver
from .benchmark import benchmark_source

from .signing import Signature,TrustStore,generate_key,sign_package,verify_package
from .secure_packages import safe_extract,write_receipt,validate_remote_source,dependency_confusion_guard

from .ed25519_signing import Ed25519Envelope,PublicTrustStore,generate_ed25519_keypair,sign_ed25519,verify_ed25519
from .registry import PackageCache,install_verified,remote_install,verify_registry_index
