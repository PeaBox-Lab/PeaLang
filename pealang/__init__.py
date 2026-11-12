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
from .web import (PeaWebApp,WebRequest,WebResponse,json_response,html_response,text_response,redirect,error_response,normalize_response)
from .analysis import (profile as analyze_profile, describe as analyze_describe, columns as analyze_columns,
    sql as analyze_sql, sql_value as analyze_sql_value,
    read_csv_file as analyze_read_csv, write_csv_file as analyze_write_csv,
    read_json_file as analyze_read_json, write_json_file as analyze_write_json,
    read_jsonl_file as analyze_read_jsonl, write_jsonl_file as analyze_write_jsonl)
from .interop import (call_python, run_command, load_native_library, call_native, http_get, http_post,
    generate_go_client, go_available, go_version, go_run)
from .numerics import (build_stats_namespace,
    linear_regression as stats_linear_regression, multiple_regression as stats_multiple_regression,
    t_test_1samp as stats_t_test_1samp, t_test_ind as stats_t_test_ind, anova_oneway as stats_anova,
    kmeans as stats_kmeans, pca as stats_pca, bootstrap as stats_bootstrap,
    normal_ppf as stats_normal_ppf, normal_cdf as stats_normal_cdf,
    pearson as stats_pearson, spearman as stats_spearman)
from .inference import (build_inference_namespace,
    confidence_interval_mean as stats_confidence_interval_mean,
    confidence_interval_proportion as stats_confidence_interval_proportion,
    cohens_d as stats_cohens_d, adjust_p_values as stats_adjust_p_values,
    mann_whitney_u as stats_mann_whitney_u, wilcoxon_signed_rank as stats_wilcoxon,
    kruskal_wallis as stats_kruskal_wallis, jarque_bera as stats_jarque_bera,
    ols as stats_ols, predict_ols as stats_predict_ols,
    acf as stats_acf, pacf as stats_pacf, ljung_box as stats_ljung_box,
    holt_linear as stats_holt_linear, holt_winters as stats_holt_winters,
    adf_test as stats_adf_test)
from .modeling import (build_modeling_namespace,
    glm as stats_glm, logistic_regression as stats_logistic_regression,
    poisson_regression as stats_poisson_regression,
    ridge_regression as stats_ridge_regression, lasso_regression as stats_lasso_regression,
    elastic_net as stats_elastic_net,
    kaplan_meier as stats_kaplan_meier, log_rank_test as stats_log_rank_test,
    cox_proportional_hazards as stats_cox,
    arima as stats_arima, auto_arima as stats_auto_arima)
from .causal import (build_causal_namespace,
    propensity_scores as stats_propensity_scores,
    covariate_balance as stats_covariate_balance,
    ipw_ate as stats_ipw_ate, aipw_ate as stats_aipw_ate,
    propensity_match as stats_propensity_match,
    difference_in_differences as stats_did,
    instrumental_variables as stats_iv,
    regression_discontinuity as stats_rdd)
from .evaluation import (build_evaluation_namespace,
    train_test_split as stats_train_test_split,
    k_fold as stats_k_fold, stratified_k_fold as stats_stratified_k_fold,
    accuracy_score as stats_accuracy, balanced_accuracy as stats_balanced_accuracy,
    precision_recall_fscore as stats_precision_recall_fscore,
    roc_curve as stats_roc_curve, roc_auc as stats_roc_auc,
    log_loss as stats_log_loss, brier_score as stats_brier_score,
    calibration_curve as stats_calibration_curve,
    mean_squared_error as stats_mse, root_mean_squared_error as stats_rmse,
    mean_absolute_error as stats_mae, median_absolute_error as stats_median_ae,
    mean_absolute_percentage_error as stats_mape,
    r2_score as stats_r2_score,
    explained_variance_score as stats_explained_variance,
    polynomial_features as stats_polynomial_features,
    label_encode as stats_label_encode, ordinal_encode as stats_ordinal_encode,
    standardize_features as stats_standardize_features,
    standardize_transform as stats_standardize_transform,
    minmax_features as stats_minmax_features,
    minmax_transform as stats_minmax_transform)
from .trees import (build_tree_namespace,
    decision_tree as stats_decision_tree,
    predict_tree as stats_predict_tree,
    tree_feature_importance as stats_tree_importance,
    random_forest as stats_random_forest,
    predict_forest as stats_predict_forest,
    forest_feature_importance as stats_forest_importance)
from .boosting import (build_boosting_namespace,
    gradient_boosting as stats_gradient_boosting,
    predict_boosting as stats_predict_boosting,
    boosting_feature_importance as stats_boosting_importance)
from .selection import (build_selection_namespace,
    cross_validate as stats_cross_validate,
    grid_search as stats_grid_search,
    random_search as stats_random_search)
from .interpret import (build_interpret_namespace,
    permutation_importance as stats_permutation_importance,
    partial_dependence as stats_partial_dependence)
from .imbalance import (build_imbalance_namespace,
    class_balance as stats_class_balance,
    random_oversample as stats_random_oversample,
    random_undersample as stats_random_undersample,
    smote as stats_smote)
from .pipeline import (build_pipeline_namespace,
    fit_pipeline as stats_fit_pipeline,
    transform_pipeline as stats_transform_pipeline)
from .ux import doctor as ux_doctor, explain_error as ux_explain
__version__ = "0.99.6"
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

from .registry_index import PackageRecord,RegistryIndex,NamespacePolicy,RegistryState,build_index,validate_index
from .registry_auth import registry_token,bearer_headers

from .compatibility import Stability,Feature,FEATURES,feature_status,stable_features,validate_deprecation
from .specification import SPEC_VERSION,verify_spec

from .stdlib import STDLIB_VERSION,MODULES,StdModuleSpec,stdlib_manifest,build_standard_library

from .type_system import GenericFunctionContract,ProtocolContract,substitute_type,infer_generic_bindings,parse_generic_functions,parse_protocols,protocol_conforms,option_type,result_type,future_type,analyze_project

from .resource_limits import ResourceLimits,ResourceUsage,ResourceBudget,ResourceLimitExceeded,estimated_size
from .structured_concurrency import CancellationScope,PeaTask,TaskGroup,gather_structured

from .native_testing import NativeTestResult,split_tests,run_source_tests,run_paths,coverage_summary
from .migration import MigrationChange,migrate_text,migrate_path

from .wasm import ABI_VERSION,WasmPolicy,WasmArtifact,compile_peac_to_wasm,inspect_wasm,browser_loader_source

from .conformance import ConformanceCase,generated_cases,differential,run_conformance,fuzz_lexer_parser,conformance_report

from .readiness import Pilot,PerformanceThresholds,ReadinessReport,default_report,save_report
from .performance_gate import RegressionGate,compare_benchmark

from .data import DataType,Field,Schema,DataFrame,LazyFrame,ConnectorSpec,ConnectorRegistry,REGISTRY,Expr,col,lit,coalesce,read as data_read,write as data_write,scan as data_scan,register_connector


from .sql import DatabaseSpec,Database,DATABASES,connect as data_connect,read_sql,execute_sql

from .connectors import ConnectorConfig,ConnectorResponse,ConnectorRegistry,RESTConnector,GraphQLConnector,REGISTRY as CONNECTORS,connector,bearer,api_key

from .cloud_connectors import ODataQuery,ODataConnector,SFTPConfig,SFTPConnector,odata,sftp

from .object_storage import ObjectStorageConnector,S3Connector,AzureBlobConnector,ADLSConnector,GCSConnector,s3,azure_blob,adls,gcs

from .enterprise_connectors import SecretRef,SecretRegistry,EnvironmentSecrets,MappingSecrets,AzureKeyVaultSecrets,AWSSecretsManager,ConnectorCapability,CertificationResult,CAPABILITIES,certify,MicrosoftGraphConnector,SharePointConnector,microsoft_graph,sharepoint

from .connector_runtime import TokenProvider,StaticTokenProvider,CallableTokenProvider,CachedTokenProvider,ConnectorProfile,HealthResult,health_check,CertificationMatrix,certify_matrix

from .analytics import mean,median,mode,quantile,variance,stddev,covariance,correlation,describe,frequencies,crosstab,rank,cumulative,rolling,outliers_iqr,profile,correlation_matrix

from .timeseries import parse_datetime,with_datetime,date_parts,resample,lag,lead,difference,pct_change,expanding,ewm,interpolate,grouped_describe,grouped_rolling

from .forecasting import mae,mse,rmse,mape,evaluate,train_test_split,linear_trend,moving_average_forecast,exponential_smoothing,seasonal_decompose,chart_series,grouped_forecast,numpy_accelerated_mean,ForecastBenchmark,benchmark_forecast

from .ml import StandardScaler,MinMaxScaler,impute,one_hot_encode,LinearRegression,LogisticRegression,regression_metrics,classification_metrics,kfold_indices,save_model,load_model,Pipeline

from .ml import LabelEncoder,stratified_split,log_loss,roc_auc,RidgeRegression,LassoRegression,MulticlassLogisticRegression,cross_validate,grid_search,coefficient_report,prediction_schema,validate_prediction_schema,model_card,reproducibility_manifest,ProductionPipeline

from .mlops import create_model_bundle,load_model_bundle,batch_predict,PredictionAudit,audited_predict,population_stability_index,categorical_drift,prediction_drift,group_fairness,optimize_threshold,PlattCalibrator,RegistryEntry,ModelRegistry,compatibility_report,inference_benchmark,create_fastapi_app

from .mlops_secure import sign_bundle,verify_bundle_signature,encrypt_artifact,decrypt_artifact,MonitoringEvent,MonitoringStore,AlertRule,Alert,evaluate_alerts,acknowledge,PromotionPolicy,can_promote,DeploymentPlan,route_variant,compare_variants,should_rollback,structured_inference_log

from .mlops_portable import PIPELINE_FORMAT,save_pipeline,load_pipeline,SQLiteMonitoringStore,load_alert_policy,deployment_manifest

from .serving import ServingConfig,PipelineRuntime,SQLiteAuditStore,create_serving_app,deploy_check,execute_deployment

from .serving_resilience import ResilienceConfig,SlidingWindowRateLimiter,StructuredLogger,ResilientRuntime,RateLimitExceeded,ConcurrencyLimitExceeded,ServingTimeout,verify_signed_pipeline,load_encrypted_pipeline,prune_audits,TraceHooks

from .distributed_serving import DistributedBackend,MemoryBackend,RedisBackend,DistributedRateLimiter,SharedDeploymentState,LatencySummary,latency_summary,load_test,KubernetesConfig,kubernetes_manifests,write_kubernetes_manifests,OpenTelemetryHooks

from .kubernetes_security import SecureKubernetesConfig,secure_kubernetes_manifests,to_yaml,write_secure_manifests,validate_manifests,DrainController,CompatibilityCase,rc_compatibility_matrix,soak_test

from .supply_chain import sha256_file,artifact_checksums,write_checksums,generate_sbom,dependency_inventory,build_provenance,verify_wheel,verify_source_archive,migration_check,reproducible_build_metadata,release_checklist,readiness_assessment,containerfile,ci_matrix

from .rc_stabilization import RC_VERSION,API_POLICY_VERSION,PublicSymbol,public_api_snapshot,compare_api_snapshots,snapshot_digest,Deprecation,deprecated,validate_deprecation_schedule,IntegrationResult,run_integration_matrix,integration_summary,upgrade_compatibility,threat_model,migration_guide,rc_gate

from .distributed_compute import PlanNode,ExecutionPlan,ComputeEngine,LocalEngine,ArrowEngine,PolarsEngine,SparkEngine,EngineRegistry,ENGINES,DistributedLazyFrame,distributed,compile_lazy,execute_plan,explain_plan
from .lineage import DatasetRef,ColumnRef,LineageEdge,LineageGraph
from .pipeline_observability import SLAPolicy,RunMetric,Alert,MetricsRegistry,SLAEvaluator,AlertRouter,AuditReport
from .dashboard import DashboardComponent,Dashboard,dashboard_from_dict,render_react

from .dashboard import DashboardFilter,DashboardState,DataBinding,apply_dashboard_filters
from .browser_repl import BrowserResult,BrowserREPL,DatasetInspector
from .jupyter import RichResult,RichDisplay,PeaKernel,kernelspec
from .model_interop import ModelInteropError,TensorSpec,TensorBridge,ONNXModel,QueryPolicy,QueryPlan,GovernedQueryPlanner
from .agent_governance import AuditEvent,GovernanceAuditStore,AuditedApprovalGate,approval_request_id
from .hardening import SecurityProbe,ProbeResult,AdversarialAgentSuite,PublicAPIGate,ReleaseThresholds,ReleaseHardeningGate,sha256_manifest
from .performance_hardening import PerformanceBudget,PerformanceSample,PerformanceProbe,PerformanceGate,BoundedLRUCache,BenchmarkStats,BenchmarkSuite,RegressionBudget,PerformanceRegressionGate,HotPathProfiler,InstrumentedLRUCache,MemoryPressureProbe,MemoryPressureResult,save_benchmark_baseline,load_benchmark_baseline
from .security_hardening import SecurityPolicy,SecurityValidator,SecurityViolation,redact_secrets,SignedAuditChain
from .integration_hardening import IntegrationError,IntegrationAuthenticationError,IntegrationTimeoutError,IntegrationRateLimitError,IntegrationUnavailableError,CircuitOpenError,CredentialProvider,EnvironmentCredentialProvider,MappingCredentialProvider,ChainedCredentialProvider,RetryPolicy as IntegrationRetryPolicy,CircuitState,CircuitBreaker,IntegrationProfile,IntegrationResult,ReliableExecutor,HealthReport,ConnectorHealthCheck

from .concurrency_resilience import CancellationReason,CancellationToken,Deadline,run_with_deadline,TaskOutcome,StructuredTaskGroup,RetryPolicyV2,RetrySafetyError,retry_async,IdempotencyStore,LifecycleState,DrainReport,GracefulShutdown,ResilienceGateBudget,ResilienceGate

from .connector_conformance import Capability,ConnectorProfile,ConformanceCase,CaseResult,CertificationReport,ConformanceSuite,SQLDialect,SQLDialectContract,SQL_DIALECTS,validate_parameter_binding,TransactionProbe,StreamEvent,StreamRecoveryModel,ObjectStoreEdgeCases,certification_gate

from .agent_safety_conformance import ToolCapability,ToolIsolationPolicy,ApprovalLedger,ExecutionBudget,BudgetTracker,AgentAuditTrail,SafeAgentExecutor,agent_safety_gate

from .tooling_conformance import Severity,DiagnosticContract,DiagnosticRegistry,ToolProtocolProfile,CompatibilityMatrix,EditorCapabilityNegotiator,BreakpointFixture,DebugSnapshot,ReproducibleDebugSession,DAPConformance,LSPConformance,tooling_certification_gate

from .rc_readiness import Severity as RCSeverity,Defect,Waiver,Evidence,RCReadiness,documentation_gate,cross_platform_gate

from .rc_hardening import Severity,Defect,Waiver,DefectRegistry,Evidence,RCReadinessGate,documentation_completeness,cross_platform_evidence

from .api_freeze import FrozenSurface,ApiFreezeManifest,FreezePolicy,BreakingChangeLedger,freeze_gate,compatibility_contract

from .rc_validation import SUPPORTED_PYTHONS,SUPPORTED_PLATFORMS,SoakEvidence,CrossPlatformSoak,UpgradeFixture,UpgradeValidation,FrozenContractSurveillance,SoakGate,RCBlocker,BlockerRegistry,rc91_gate,evidence_digest

from .rc_validation_ii import TimedEvidence,EvidenceFreshness,UpgradeDrill,UpgradeDrillSuite,CompatibilityObservation,DriftSurveillance,TrendPoint,SoakTrendGate,EcosystemCertification,EcosystemGate,RecoveryDrill,RecoveryGate,Waiver,WaiverLifecycle,rc92_gate,certification_digest
