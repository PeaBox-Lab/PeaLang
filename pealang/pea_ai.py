"""LLM-native primitives and agent framework for PeaLang (Phase 4).

Provides first-class support for LLM operations, agent workflows, model ops,
eval/guardrails, and data-centric AI patterns.
"""

from __future__ import annotations

import json
import os
import time
import hashlib
import hmac
import base64
import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union
from pathlib import Path
from abc import ABC, abstractmethod


# ============================================================================
# LLM Provider Abstractions
# ============================================================================

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> str:
        """Generate a completion."""
        pass
    
    @abstractmethod
    def complete_structured(self, prompt: str, schema: dict, **kwargs) -> dict:
        """Generate a structured completion matching the given JSON schema."""
        pass
    
    @abstractmethod
    def embed(self, text: str | list[str], **kwargs) -> list[float] | list[list[float]]:
        """Generate embeddings."""
        pass
    
    @abstractmethod
    def token_count(self, text: str) -> int:
        """Count tokens in text."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def __init__(self, api_key: str | None = None, model: str = "gpt-4", 
                 base_url: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
        
        if not self.api_key:
            raise ValueError("OpenAI API key required")
    
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
    
    def complete(self, prompt: str, **kwargs) -> str:
        import urllib.request
        import urllib.error
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }
        
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(data).encode(),
            headers=self._headers(),
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"OpenAI API error: {e.read().decode()}")
    
    def complete_structured(self, prompt: str, schema: dict, **kwargs) -> dict:
        import urllib.request
        
        # Use function calling for structured output
        function = {
            "name": "structured_output",
            "description": "Return structured output matching schema",
            "parameters": schema
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "functions": [function],
            "function_call": {"name": "structured_output"},
            "temperature": kwargs.get("temperature", 0.0),
        }
        
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(data).encode(),
            headers=self._headers(),
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
                args = result["choices"][0]["message"].get("function_call", {}).get("arguments", "{}")
                return json.loads(args)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"OpenAI API error: {e.read().decode()}")
    
    def embed(self, text: str | list[str], **kwargs) -> list[float] | list[list[float]]:
        import urllib.request
        
        texts = [text] if isinstance(text, str) else text
        data = {"model": kwargs.get("embed_model", "text-embedding-3-small"), "input": texts}
        
        req = urllib.request.Request(
            f"{self.base_url}/embeddings",
            data=json.dumps(data).encode(),
            headers=self._headers(),
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
                embeddings = [d["embedding"] for d in result["data"]]
                return embeddings[0] if len(embeddings) == 1 else embeddings
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"OpenAI API error: {e.read().decode()}")
    
    def token_count(self, text: str) -> int:
        try:
            import tiktoken
            enc = tiktoken.encoding_for_model(self.model)
            return len(enc.encode(text))
        except ImportError:
            # Rough approximation: ~4 chars per token
            return len(text) // 4


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""
    
    def __init__(self, api_key: str | None = None, model: str = "claude-3-opus-20240229"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("Anthropic API key required")
    
    def _headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    
    def complete(self, prompt: str, **kwargs) -> str:
        import urllib.request
        
        data = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", 2048),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
        }
        
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(data).encode(),
            headers=self._headers(),
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
                return result["content"][0]["text"]
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Anthropic API error: {e.read().decode()}")
    
    def complete_structured(self, prompt: str, schema: dict, **kwargs) -> dict:
        # Use JSON mode for structured output
        structured_prompt = f"{prompt}\n\nReturn ONLY valid JSON matching this schema: {json.dumps(schema)}"
        result = self.complete(structured_prompt, temperature=0.0, **kwargs)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            match = re.search(r'\{.*\}', result, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError(f"Could not parse structured output: {result}")
    
    def embed(self, text: str | list[str], **kwargs) -> list[float] | list[list[float]]:
        raise NotImplementedError("Anthropic doesn't provide embeddings API")
    
    def token_count(self, text: str) -> int:
        return len(text) // 4  # Rough approximation


class LocalProvider(LLMProvider):
    """Local LLM provider (Ollama, llama.cpp, etc.)."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
    
    def complete(self, prompt: str, **kwargs) -> str:
        import urllib.request
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 2048),
            }
        }
        
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode())
                return result.get("response", "")
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Local LLM error: {e.read().decode()}")
    
    def complete_structured(self, prompt: str, schema: dict, **kwargs) -> dict:
        structured_prompt = f"{prompt}\n\nReturn ONLY valid JSON matching this schema: {json.dumps(schema)}"
        result = self.complete(structured_prompt, temperature=0.0, **kwargs)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', result, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError(f"Could not parse structured output: {result}")
    
    def embed(self, text: str | list[str], **kwargs) -> list[float] | list[list[float]]:
        import urllib.request
        
        texts = [text] if isinstance(text, str) else text
        embeddings = []
        for t in texts:
            data = {"model": kwargs.get("embed_model", "nomic-embed-text"), "prompt": t}
            req = urllib.request.Request(
                f"{self.base_url}/api/embeddings",
                data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    result = json.loads(resp.read().decode())
                    embeddings.append(result.get("embedding", []))
            except urllib.error.HTTPError as e:
                raise RuntimeError(f"Local embedding error: {e.read().decode()}")
        
        return embeddings[0] if len(embeddings) == 1 else embeddings
    
    def token_count(self, text: str) -> int:
        return len(text) // 4


# Provider registry
_PROVIDERS: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "local": LocalProvider,
}


def register_provider(name: str, provider_class: type[LLMProvider]):
    """Register a custom LLM provider."""
    _PROVIDERS[name] = provider_class


def get_provider(name: str, **kwargs) -> LLMProvider:
    """Get an LLM provider instance."""
    if name not in _PROVIDERS:
        raise ValueError(f"Unknown provider: {name}. Available: {list(_PROVIDERS.keys())}")
    return _PROVIDERS[name](**kwargs)


# ============================================================================
# Prompt Templates & Chaining
# ============================================================================

@dataclass
class PromptTemplate:
    """Reusable prompt template with variable substitution."""
    template: str
    input_variables: list[str] = field(default_factory=list)
    
    def format(self, **kwargs) -> str:
        """Format the template with provided variables."""
        missing = set(self.input_variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing variables: {missing}")
        return self.template.format(**kwargs)
    
    @classmethod
    def from_file(cls, path: str, input_variables: list[str] | None = None) -> "PromptTemplate":
        """Load template from file."""
        content = Path(path).read_text(encoding="utf-8")
        if input_variables is None:
            # Extract variables from template
            import re
            input_variables = list(set(re.findall(r'\{(\w+)\}', content)))
        return cls(template=content, input_variables=input_variables)


@dataclass
class Chain:
    """Chain of LLM operations."""
    steps: list[Callable] = field(default_factory=list)
    
    def add(self, step: Callable) -> "Chain":
        self.steps.append(step)
        return self
    
    def run(self, input_data: Any) -> Any:
        result = input_data
        for step in self.steps:
            result = step(result)
        return result
    
    async def arun(self, input_data: Any) -> Any:
        result = input_data
        for step in self.steps:
            if asyncio.iscoroutinefunction(step):
                result = await step(result)
            else:
                result = step(result)
        return result


def create_llm_chain(provider: LLMProvider, template: PromptTemplate, 
                     output_key: str = "output") -> Callable:
    """Create a chain step that uses an LLM with a prompt template."""
    def step(input_data: dict) -> dict:
        prompt = template.format(**input_data)
        result = provider.complete(prompt)
        return {**input_data, output_key: result}
    return step


def create_structured_chain(provider: LLMProvider, template: PromptTemplate, 
                            schema: dict, output_key: str = "output") -> Callable:
    """Create a chain step that uses structured LLM output."""
    def step(input_data: dict) -> dict:
        prompt = template.format(**input_data)
        result = provider.complete_structured(prompt, schema)
        return {**input_data, output_key: result}
    return step


# ============================================================================
# Agent Framework
# ============================================================================

@dataclass
class Tool:
    """Agent tool definition."""
    name: str
    description: str
    function: Callable
    parameters: dict  # JSON schema
    
    def to_openai_function(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


@dataclass
class Agent:
    """ReAct-style agent with tools and memory."""
    name: str
    provider: LLMProvider
    tools: list[Tool] = field(default_factory=list)
    system_prompt: str = ""
    max_iterations: int = 10
    memory: list[dict] = field(default_factory=list)
    
    def add_tool(self, tool: Tool) -> "Agent":
        self.tools.append(tool)
        return self
    
    def _get_tool_descriptions(self) -> str:
        return "\n".join([
            f"- {t.name}: {t.description}" for t in self.tools
        ])
    
    def _get_tool_schemas(self) -> list[dict]:
        return [t.to_openai_function() for t in self.tools]
    
    def run(self, task: str) -> dict:
        """Run the agent on a task using ReAct pattern."""
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": task})
        
        for iteration in range(self.max_iterations):
            # Get available tools
            tool_descs = self._get_tool_descriptions()
            tool_schemas = self._get_tool_schemas()
            
            # Build prompt
            prompt = f"""You are {self.name}. You have access to these tools:
{tool_descs}

Current task: {task}

Previous actions: {json.dumps(self.memory[-5:]) if self.memory else "None"}

Think step by step. You can either:
1. Call a tool using the function calling format
2. Provide the final answer

What do you do next?"""
            
            # Call LLM
            if tool_schemas:
                result = self.provider.complete_structured(
                    prompt,
                    schema={
                        "type": "object",
                        "properties": {
                            "thought": {"type": "string"},
                            "action": {"type": "string", "enum": [t.name for t in self.tools] + ["finish"]},
                            "action_input": {"type": "object"},
                        },
                        "required": ["thought", "action"]
                    }
                )
            else:
                result = self.provider.complete(prompt, temperature=0.7)
                result = {"thought": result, "action": "finish", "action_input": {}}
            
            thought = result.get("thought", "")
            action = result.get("action", "finish")
            action_input = result.get("action_input", {})
            
            self.memory.append({
                "iteration": iteration,
                "thought": thought,
                "action": action,
                "action_input": action_input
            })
            
            if action == "finish":
                return {
                    "result": thought,
                    "iterations": iteration + 1,
                    "memory": self.memory
                }
            
            # Execute tool
            tool = next((t for t in self.tools if t.name == action), None)
            if not tool:
                error = f"Unknown tool: {action}"
                self.memory.append({"error": error})
                continue
            
            try:
                observation = tool.function(**action_input)
            except Exception as e:
                observation = f"Error: {str(e)}"
            
            self.memory.append({"observation": str(observation)})
        
        return {
            "result": "Max iterations reached",
            "iterations": self.max_iterations,
            "memory": self.memory
        }


def create_react_agent(provider: LLMProvider, name: str, tools: list[Tool],
                       system_prompt: str = "") -> Agent:
    """Create a ReAct agent with tools."""
    return Agent(
        name=name,
        provider=provider,
        tools=tools,
        system_prompt=system_prompt
    )


# ============================================================================
# Model Operations
# ============================================================================

@dataclass
class ModelConfig:
    """Model training/inference configuration."""
    name: str
    provider: str
    model_id: str
    parameters: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


@dataclass
class TrainingRun:
    """Record of a model training run."""
    model_id: str
    config: ModelConfig
    dataset: str
    metrics: dict = field(default_factory=dict)
    artifacts: dict = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    status: str = "running"
    error: str | None = None
    
    def complete(self, metrics: dict, artifacts: dict):
        self.completed_at = time.time()
        self.metrics = metrics
        self.artifacts = artifacts
        self.status = "completed"
    
    def fail(self, error: str):
        self.completed_at = time.time()
        self.error = error
        self.status = "failed"


class ModelRegistry:
    """Registry for model versions and metadata."""
    
    def __init__(self, storage_path: str = "./models"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.index_path = self.storage_path / "registry.json"
        self._index = self._load_index()
    
    def _load_index(self) -> dict:
        if self.index_path.exists():
            return json.loads(self.index_path.read_text())
        return {"models": {}, "versions": {}}
    
    def _save_index(self):
        self.index_path.write_text(json.dumps(self._index, indent=2))
    
    def register(self, model_id: str, config: ModelConfig, 
                 artifacts: dict | None = None) -> str:
        """Register a new model version."""
        version = f"v{len(self._index['versions'].get(model_id, [])) + 1}"
        
        entry = {
            "model_id": model_id,
            "version": version,
            "config": config.__dict__ if hasattr(config, '__dict__') else config,
            "artifacts": artifacts or {},
            "registered_at": time.time(),
            "status": "staging"
        }
        
        if model_id not in self._index["versions"]:
            self._index["versions"][model_id] = []
        self._index["versions"][model_id].append(entry)
        self._index["models"][model_id] = entry
        self._save_index()
        
        return version
    
    def promote(self, model_id: str, version: str, stage: str = "production"):
        """Promote a model version to a stage."""
        for v in self._index["versions"].get(model_id, []):
            if v["version"] == version:
                v["stage"] = stage
                self._save_index()
                return True
        return False
    
    def get(self, model_id: str, version: str | None = None) -> dict | None:
        """Get model info."""
        if version:
            for v in self._index["versions"].get(model_id, []):
                if v["version"] == version:
                    return v
            return None
        return self._index["models"].get(model_id)
    
    def list_versions(self, model_id: str) -> list[dict]:
        return self._index["versions"].get(model_id, [])


def export_model(model_id: str, version: str, format: str = "onnx") -> str:
    """Export model to specified format."""
    # Placeholder - would integrate with ONNX, TorchScript, etc.
    return f"Exported {model_id}:{version} to {format}"


def deploy_model(model_id: str, version: str, target: str = "local") -> dict:
    """Deploy model to target platform."""
    # Placeholder - would integrate with K8s, Cloud Run, Lambda, etc.
    return {
        "model_id": model_id,
        "version": version,
        "target": target,
        "endpoint": f"http://{model_id}-{version}.local",
        "status": "deployed"
    }


# ============================================================================
# Evaluation & Guardrails
# ============================================================================

@dataclass
class EvalCase:
    """Single evaluation case."""
    input: str
    expected: str | dict
    metadata: dict = field(default_factory=dict)


@dataclass
class EvalResult:
    """Result of an evaluation."""
    case: EvalCase
    output: str | dict
    passed: bool
    score: float
    details: dict = field(default_factory=dict)


class Evaluator:
    """Base evaluator class."""
    
    def evaluate(self, case: EvalCase, output: str | dict) -> EvalResult:
        raise NotImplementedError


class ExactMatchEvaluator(Evaluator):
    """Exact string match evaluator."""
    
    def evaluate(self, case: EvalCase, output: str | dict) -> EvalResult:
        expected = case.expected
        if isinstance(output, dict) and isinstance(expected, dict):
            passed = output == expected
        else:
            passed = str(output).strip() == str(expected).strip()
        return EvalResult(case=case, output=output, passed=passed, score=1.0 if passed else 0.0)


class ContainsEvaluator(Evaluator):
    """Substring/containment evaluator."""
    
    def evaluate(self, case: EvalCase, output: str | dict) -> EvalResult:
        expected = str(case.expected)
        actual = str(output)
        passed = expected.lower() in actual.lower()
        return EvalResult(case=case, output=output, passed=passed, score=1.0 if passed else 0.0)


class LLMEvaluator(Evaluator):
    """LLM-based evaluator for semantic comparison."""
    
    def __init__(self, provider: LLMProvider):
        self.provider = provider
    
    def evaluate(self, case: EvalCase, output: str | dict) -> EvalResult:
        prompt = f"""Evaluate if the output matches the expected result.

Expected: {case.expected}
Actual: {output}

Return JSON: {{"score": 0-1, "passed": true/false, "reasoning": "..."}}"""
        
        result = self.provider.complete_structured(prompt, schema={
            "type": "object",
            "properties": {
                "score": {"type": "number", "minimum": 0, "maximum": 1},
                "passed": {"type": "boolean"},
                "reasoning": {"type": "string"}
            },
            "required": ["score", "passed", "reasoning"]
        })
        
        return EvalResult(
            case=case,
            output=output,
            passed=result["passed"],
            score=result["score"],
            details={"reasoning": result["reasoning"]}
        )


class Guardrail:
    """Base guardrail class."""
    
    def check(self, text: str) -> tuple[bool, str | None]:
        """Check if text passes guardrail. Returns (passed, error_message)."""
        raise NotImplementedError


class PIIGuardrail(Guardrail):
    """PII detection guardrail."""
    
    PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        "api_key": r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)["\s:=]+[\w-]{20,}',
    }
    
    def __init__(self, patterns: dict[str, str] | None = None):
        self.patterns = patterns or self.PATTERNS
        import re
        self._compiled = {k: re.compile(v) for k, v in self.patterns.items()}
    
    def check(self, text: str) -> tuple[bool, str | None]:
        import re
        for name, pattern in self._compiled.items():
            if pattern.search(text):
                return False, f"PII detected: {name}"
        return True, None


class SecretGuardrail(Guardrail):
    """Secret/credential detection guardrail."""
    
    PATTERNS = {
        "aws_key": r'AKIA[0-9A-Z]{16}',
        "github_token": r'ghp_[A-Za-z0-9]{36}',
        "slack_token": r'xoxb-\d+-\d+-[A-Za-z0-9]+',
        "generic_secret": r'(?i)(password|secret|token|key)["\s:=]+[\w-]{16,}',
    }
    
    def check(self, text: str) -> tuple[bool, str | None]:
        import re
        for name, pattern in self.PATTERNS.items():
            if re.search(pattern, text):
                return False, f"Secret detected: {name}"
        return True, None


class ToxicityGuardrail(Guardrail):
    """Toxicity/content safety guardrail."""
    
    def __init__(self, provider: LLMProvider | None = None, threshold: float = 0.7):
        self.provider = provider
        self.threshold = threshold
    
    def check(self, text: str) -> tuple[bool, str | None]:
        if not self.provider:
            # Simple keyword-based check as fallback
            toxic_words = ["hate", "violence", "illegal", "harmful"]
            for word in toxic_words:
                if word.lower() in text.lower():
                    return False, f"Potential toxic content: {word}"
            return True, None
        
        # Use LLM for toxicity classification
        prompt = f"""Classify the following text for toxicity.
        
Text: {text}

Return JSON: {{"toxic": true/false, "score": 0-1, "categories": [...]}}"""
        
        result = self.provider.complete_structured(prompt, schema={
            "type": "object",
            "properties": {
                "toxic": {"type": "boolean"},
                "score": {"type": "number", "minimum": 0, "maximum": 1},
                "categories": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["toxic", "score", "categories"]
        })
        
        if result["toxic"] and result["score"] >= self.threshold:
            return False, f"Toxic content detected: {result['categories']}"
        return True, None


class GuardrailPipeline:
    """Pipeline of guardrails."""
    
    def __init__(self, guardrails: list[Guardrail]):
        self.guardrails = guardrails
    
    def check(self, text: str) -> tuple[bool, list[str]]:
        errors = []
        for gr in self.guardrails:
            passed, error = gr.check(text)
            if not passed:
                errors.append(error)
        return len(errors) == 0, errors


# ============================================================================
# Data-Centric AI
# ============================================================================

@dataclass
class DatasetVersion:
    """Dataset version with metadata."""
    name: str
    version: str
    path: str
    schema: dict = field(default_factory=dict)
    stats: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    parent_version: str | None = None
    tags: list[str] = field(default_factory=list)


class DatasetRegistry:
    """Dataset versioning and lineage tracking."""
    
    def __init__(self, storage_path: str = "./datasets"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.index_path = self.storage_path / "registry.json"
        self._index = self._load_index()
    
    def _load_index(self) -> dict:
        if self.index_path.exists():
            return json.loads(self.index_path.read_text())
        return {"datasets": {}}
    
    def _save_index(self):
        self.index_path.write_text(json.dumps(self._index, indent=2))
    
    def register(self, dataset: DatasetVersion) -> str:
        if dataset.name not in self._index["datasets"]:
            self._index["datasets"][dataset.name] = {"versions": {}}
        
        self._index["datasets"][dataset.name]["versions"][dataset.version] = dataset.__dict__
        self._save_index()
        return dataset.version
    
    def get(self, name: str, version: str | None = None) -> DatasetVersion | None:
        ds = self._index["datasets"].get(name)
        if not ds:
            return None
        if version:
            v = ds["versions"].get(version)
            return DatasetVersion(**v) if v else None
        # Return latest
        versions = ds["versions"]
        if not versions:
            return None
        latest = max(versions.keys())
        return DatasetVersion(**versions[latest])
    
    def list_versions(self, name: str) -> list[str]:
        return list(self._index["datasets"].get(name, {}).get("versions", {}).keys())


def active_learning_loop(model, dataset, query_strategy, budget: int) -> list:
    """Active learning loop for labeling."""
    labeled = []
    unlabeled = list(dataset)
    
    for _ in range(budget):
        if not unlabeled:
            break
        
        # Query strategy selects most informative samples
        idx = query_strategy(model, unlabeled)
        sample = unlabeled.pop(idx)
        labeled.append(sample)
        
        # Retrain model (simplified)
        model.fit(labeled)
    
    return labeled


# ============================================================================
# GPU/Accelerator Support
# ============================================================================

class AcceleratorConfig:
    """Configuration for accelerator backends."""
    
    def __init__(self, backend: str = "cpu", device_id: int = 0, 
                 precision: str = "fp32", memory_limit: str | None = None):
        self.backend = backend  # cpu, cuda, rocm, metal
        self.device_id = device_id
        self.precision = precision  # fp32, fp16, bf16, int8
        self.memory_limit = memory_limit
    
    def __str__(self):
        return f"{self.backend}:{self.device_id} ({self.precision})"


def get_accelerator(config: AcceleratorConfig):
    """Get accelerator backend instance."""
    if config.backend == "cpu":
        return CPUAccelerator()
    elif config.backend == "cuda":
        return CUDAAccelerator(config.device_id, config.precision)
    elif config.backend == "rocm":
        return ROCmAccelerator(config.device_id, config.precision)
    elif config.backend == "metal":
        return MetalAccelerator(config.device_id, config.precision)
    else:
        raise ValueError(f"Unknown backend: {config.backend}")


class BaseAccelerator(ABC):
    @abstractmethod
    def matmul(self, a, b): pass
    @abstractmethod
    def to_device(self, tensor): pass
    @abstractmethod
    def from_device(self, tensor): pass


class CPUAccelerator(BaseAccelerator):
    def matmul(self, a, b):
        import numpy as np
        return np.matmul(a, b)
    
    def to_device(self, tensor):
        return tensor
    
    def from_device(self, tensor):
        return tensor


class CUDAAccelerator(BaseAccelerator):
    def __init__(self, device_id: int = 0, precision: str = "fp32"):
        try:
            import cupy as cp
            self.cp = cp
            self.device = cp.cuda.Device(device_id)
            self.device.use()
            self.precision = precision
        except ImportError:
            raise RuntimeError("CuPy not installed. Install with: pip install cupy")
    
    def matmul(self, a, b):
        a_gpu = self.cp.asarray(a)
        b_gpu = self.cp.asarray(b)
        result = self.cp.matmul(a_gpu, b_gpu)
        return self.cp.asnumpy(result)
    
    def to_device(self, tensor):
        return self.cp.asarray(tensor)
    
    def from_device(self, tensor):
        return self.cp.asnumpy(tensor)


class ROCmAccelerator(BaseAccelerator):
    """AMD ROCm accelerator (uses hipfy or cupy with ROCm)."""
    def __init__(self, device_id: int = 0, precision: str = "fp32"):
        try:
            import cupy as cp
            self.cp = cp
            self.precision = precision
        except ImportError:
            raise RuntimeError("ROCm support requires CuPy with ROCm")
    
    def matmul(self, a, b):
        a_gpu = self.cp.asarray(a)
        b_gpu = self.cp.asarray(b)
        result = self.cp.matmul(a_gpu, b_gpu)
        return self.cp.asnumpy(result)
    
    def to_device(self, tensor):
        return self.cp.asarray(tensor)
    
    def from_device(self, tensor):
        return self.cp.asnumpy(tensor)


class MetalAccelerator(BaseAccelerator):
    """Apple Metal accelerator (MPS)."""
    def __init__(self, device_id: int = 0, precision: str = "fp32"):
        try:
            import torch
            if not torch.backends.mps.is_available():
                raise RuntimeError("MPS not available")
            self.device = torch.device("mps")
            self.precision = precision
        except ImportError:
            raise RuntimeError("PyTorch with MPS required")
    
    def matmul(self, a, b):
        import torch
        a_t = torch.from_numpy(a).to(self.device)
        b_t = torch.from_numpy(b).to(self.device)
        result = torch.matmul(a_t, b_t)
        return result.cpu().numpy()
    
    def to_device(self, tensor):
        import torch
        return torch.from_numpy(tensor).to(self.device)
    
    def from_device(self, tensor):
        return tensor.cpu().numpy()


def jit_compile(target: str = "cuda"):
    """Decorator for JIT compilation to accelerator target."""
    def decorator(func):
        if target == "cuda":
            try:
                import numba
                return numba.cuda.jit(func)
            except ImportError:
                pass
        return func
    return decorator


# ============================================================================
# Namespace Builder
# ============================================================================

def build_pea_ai_namespace() -> dict[str, Any]:
    """Build the pea_ai namespace for the analysis module."""
    return {
        # Providers
        "OpenAIProvider": OpenAIProvider,
        "AnthropicProvider": AnthropicProvider,
        "LocalProvider": LocalProvider,
        "get_provider": get_provider,
        "register_provider": register_provider,
        
        # Templates & Chains
        "PromptTemplate": PromptTemplate,
        "Chain": Chain,
        "create_llm_chain": create_llm_chain,
        "create_structured_chain": create_structured_chain,
        
        # Agents
        "Tool": Tool,
        "Agent": Agent,
        "create_react_agent": create_react_agent,
        
        # Model Ops
        "ModelConfig": ModelConfig,
        "TrainingRun": TrainingRun,
        "ModelRegistry": ModelRegistry,
        "export_model": export_model,
        "deploy_model": deploy_model,
        
        # Evaluation
        "EvalCase": EvalCase,
        "EvalResult": EvalResult,
        "ExactMatchEvaluator": ExactMatchEvaluator,
        "ContainsEvaluator": ContainsEvaluator,
        "LLMEvaluator": LLMEvaluator,
        
        # Guardrails
        "PIIGuardrail": PIIGuardrail,
        "SecretGuardrail": SecretGuardrail,
        "ToxicityGuardrail": ToxicityGuardrail,
        "GuardrailPipeline": GuardrailPipeline,
        
        # Data-Centric AI
        "DatasetVersion": DatasetVersion,
        "DatasetRegistry": DatasetRegistry,
        "active_learning_loop": active_learning_loop,
        
        # Accelerators
        "AcceleratorConfig": AcceleratorConfig,
        "get_accelerator": get_accelerator,
        "jit_compile": jit_compile,
        "CPUAccelerator": CPUAccelerator,
        "CUDAAccelerator": CUDAAccelerator,
        "ROCmAccelerator": ROCmAccelerator,
        "MetalAccelerator": MetalAccelerator,
    }