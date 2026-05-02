# PROOF: [L2/インフラ] <- mekhane/api/routes/ccl.py
# PURPOSE: /api/ccl/* — CCL パース/実行、WF レジストリ
"""
CCL Routes — Hermēneus dispatch/executor と WorkflowRegistry を API 化

POST /api/ccl/parse     — CCL 式 → AST ツリー + WF パス
POST /api/ccl/execute   — CCL 式 → Coordinator 経由実行
GET  /api/wf/list       — WorkflowRegistry 全 WF 一覧
GET  /api/wf/{name}     — WF 定義詳細
"""

from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field


# --- Pydantic Models ---

# PURPOSE: の統一的インターフェースを実現する
class CCLParseRequest(BaseModel):
    ccl: str = Field(description="CCL 式 (例: '/noe+ >> /met')")
    invocation_mode: str = Field(
        default="explicit",
        description="contract enforcement mode: explicit|implicit|internal",
    )

# PURPOSE: の統一的インターフェースを実現する
class CCLParseResponse(BaseModel):
    success: bool
    ccl: str
    tree: Optional[str] = None
    workflows: list[str] = []
    wf_paths: dict[str, str] = {}
    plan_template: Optional[str] = None
    contract: dict[str, Any] = {}
    error: Optional[str] = None

# PURPOSE: の統一的インターフェースを実現する
class CCLExecuteRequest(BaseModel):
    ccl: str = Field(description="CCL 式")
    context: str = Field(default="", description="実行コンテキスト")
    invocation_mode: str = Field(
        default="explicit",
        description="contract enforcement mode: explicit|implicit|internal",
    )

# PURPOSE: の統一的インターフェースを実現する
class CCLExecuteResponse(BaseModel):
    success: bool
    ccl: str
    result: Optional[dict[str, Any]] = None
    contract: dict[str, Any] = {}
    validation: dict[str, Any] = {}
    error: Optional[str] = None

# PURPOSE: の統一的インターフェースを実現する
class WFSummary(BaseModel):
    name: str
    description: str
    ccl: str = ""
    modes: list[str] = []

# PURPOSE: の統一的インターフェースを実現する
class WFListResponse(BaseModel):
    total: int
    workflows: list[WFSummary]

# PURPOSE: の統一的インターフェースを実現する
class WFDetailResponse(BaseModel):
    name: str
    description: str
    ccl: str = ""
    stages: list[dict[str, Any]] = []
    modes: list[str] = []
    source_path: Optional[str] = None
    raw_content: Optional[str] = None
    metadata: dict[str, Any] = {}


# --- Router ---

router = APIRouter(tags=["ccl"])


# PURPOSE: ccl を解析する
@router.post("/ccl/parse", response_model=CCLParseResponse)
async def parse_ccl(request: CCLParseRequest) -> CCLParseResponse:
    """CCL 式をパースし、AST ツリー + WF パスを返す。"""
    try:
        from hermeneus.src.ccl_contracts import compile_ccl_contract
        from hermeneus.src.dispatch import dispatch
        result = dispatch(
            request.ccl,
            invocation_mode=request.invocation_mode,
        )
        contract_dict = result.get("contract")
        if not isinstance(contract_dict, dict) or not contract_dict:
            contract = compile_ccl_contract(
                request.ccl,
                invocation_mode=request.invocation_mode,
            )
            contract_dict = contract.to_dict()
        return CCLParseResponse(
            success=result.get("success", False),
            ccl=request.ccl,
            tree=result.get("tree"),
            workflows=result.get("workflows", []),
            wf_paths=result.get("wf_paths", {}),
            plan_template=result.get("plan_template"),
            contract=contract_dict,
            error=result.get("error"),
        )
    except Exception as e:  # noqa: BLE001
        return CCLParseResponse(
            success=False,
            ccl=request.ccl,
            error=str(e),
        )


# PURPOSE: ccl を実行する
@router.post("/ccl/execute", response_model=CCLExecuteResponse)
async def execute_ccl(request: CCLExecuteRequest) -> CCLExecuteResponse:
    """CCL 式を Synergeia Coordinator 経由で実行する。"""
    try:
        from hermeneus.src.ccl_contracts import (
            compile_ccl_contract,
            extract_text_payload,
            validate_ccl_contract,
        )
        from mekhane.ccl.executor import (
            ZeroTrustCCLExecutor,
            build_zero_trust_blocked_payload,
        )
        from synergeia.bridge import dispatch as synergeia_dispatch
        try:
            contract = compile_ccl_contract(
                request.ccl,
                invocation_mode=request.invocation_mode,
            )
        except Exception as exc:  # noqa: BLE001
            if request.invocation_mode == "explicit":
                blocked_payload = {
                    "status": "blocked",
                    "error_type": "ccl_contract_blocked",
                    "requested_ccl": request.ccl,
                    "normalized_ccl": request.ccl,
                    "unmet_requirements": ["contract_compile"],
                    "blocking_reason": f"CCL contract compile failed: {exc}",
                    "safe_next_step": "CCL contract compile が通るまで実行を停止",
                }
                return CCLExecuteResponse(
                    success=False,
                    ccl=request.ccl,
                    result=blocked_payload,
                    contract={},
                    validation={},
                    error="ccl_contract_blocked",
                )
            raise
        zero_trust_executor = None
        zero_trust_context = None
        if request.invocation_mode == "explicit":
            zero_trust_executor = ZeroTrustCCLExecutor()
            zero_trust_context, zero_trust_preflight = zero_trust_executor.preflight(
                request.ccl
            )
            if zero_trust_preflight is not None:
                zero_trust_validation = zero_trust_preflight.to_dict()
                zero_trust_validation["contract_trace"] = (
                    zero_trust_context.contract_trace
                )
                return CCLExecuteResponse(
                    success=False,
                    ccl=request.ccl,
                    result=build_zero_trust_blocked_payload(
                        request.ccl,
                        zero_trust_context,
                        zero_trust_preflight,
                    ),
                    contract=contract.to_dict(),
                    validation={
                        "contract": {},
                        "zero_trust": zero_trust_validation,
                        "contract_trace": zero_trust_context.contract_trace,
                    },
                    error="ccl_contract_blocked",
                )
        result = synergeia_dispatch(
            ccl=request.ccl,
            context=request.context,
            execute=True,
        )
        result_dict = (
            result.to_dict() if hasattr(result, 'to_dict') else {"status": str(result)}
        )
        result_text = extract_text_payload(result_dict)
        contract_validation = validate_ccl_contract(contract, result_dict)
        zero_trust_validation = None
        if zero_trust_executor is not None and zero_trust_context is not None:
            zero_trust_validation = zero_trust_executor.validate(
                result_text,
                zero_trust_context,
            )
        validation_payload = {
            "contract": contract_validation.to_dict(),
        }
        if zero_trust_validation is not None and zero_trust_context is not None:
            validation_payload["zero_trust"] = zero_trust_validation.to_dict()
            validation_payload["contract_trace"] = zero_trust_context.contract_trace
        if (
            not contract_validation.is_compliant
            and request.invocation_mode == "explicit"
        ):
            return CCLExecuteResponse(
                success=False,
                ccl=request.ccl,
                result=contract_validation.blocked_payload(),
                contract=contract.to_dict(),
                validation=validation_payload,
                error="ccl_contract_blocked",
            )
        if (
            zero_trust_validation is not None
            and not zero_trust_validation.valid
            and request.invocation_mode == "explicit"
        ):
            return CCLExecuteResponse(
                success=False,
                ccl=request.ccl,
                result=build_zero_trust_blocked_payload(
                    request.ccl,
                    zero_trust_context,
                    zero_trust_validation,
                ),
                contract=contract.to_dict(),
                validation=validation_payload,
                error="ccl_contract_blocked",
            )
        return CCLExecuteResponse(
            success=True,
            ccl=request.ccl,
            result=result_dict,
            contract=contract.to_dict(),
            validation=validation_payload,
        )
    except Exception as e:  # noqa: BLE001
        return CCLExecuteResponse(
            success=False,
            ccl=request.ccl,
            contract={},
            validation={},
            error=str(e),
        )


# PURPOSE: ccl の list workflows 処理を実行する
@router.get("/wf/list", response_model=WFListResponse)
async def list_workflows() -> WFListResponse:
    """WorkflowRegistry から全 WF 一覧を取得。"""
    try:
        from hermeneus.src.registry import get_default_registry
        registry = get_default_registry()
        all_wfs = registry.load_all()

        summaries = []
        for wf in all_wfs.values():
            summaries.append(WFSummary(
                name=wf.name,
                description=wf.description,
                ccl=wf.ccl,
                modes=wf.modes,
            ))

        return WFListResponse(
            total=len(summaries),
            workflows=sorted(summaries, key=lambda w: w.name),
        )
    except Exception as e:  # noqa: BLE001
        return WFListResponse(total=0, workflows=[])


# PURPOSE: workflow を取得する
@router.get("/wf/{name}", response_model=WFDetailResponse)
async def get_workflow(name: str) -> WFDetailResponse:
    """WF 定義の詳細を取得。"""
    try:
        from hermeneus.src.registry import get_default_registry
        registry = get_default_registry()
        wf = registry.get(name)

        if wf is None:
            return WFDetailResponse(
                name=name,
                description="Not found",
                metadata={"error": f"Workflow '{name}' not found"},
            )

        return WFDetailResponse(
            name=wf.name,
            description=wf.description,
            ccl=wf.ccl,
            stages=[{"name": s.name, "description": s.description} for s in wf.stages],
            modes=wf.modes,
            source_path=str(wf.source_path) if wf.source_path else None,
            metadata=wf.metadata,
        )
    except Exception as e:  # noqa: BLE001
        return WFDetailResponse(
            name=name,
            description="Error",
            metadata={"error": str(e)},
        )
