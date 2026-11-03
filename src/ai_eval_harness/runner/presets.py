from __future__ import annotations

"""内置模拟目标服务：用于 POC 演示与离线评测（无需真实模型/内网）。

真实交付时，把 RAG/Text2SQL/Agent 服务封装成实现 `TargetService.answer()`
的适配器即可（见 examples/adapter_example.py）。
"""

from .services import MockService


def build_mock_rag_v0() -> MockService:
    """知识库 RAG v0：域外问题不拒答、涉密回答不完整（用于对比基线）。"""
    return MockService(
        name="rag-v0",
        rules={
            "报销流程": ("三级审批（部门-财务-主管）", False),
            "年假最多可以累积": ("累计最多 15 天", False),
            "涉密文件的借阅": ("需审批", False),
            "今天食堂": ("今天有火锅", False),
        },
    )


def build_mock_rag_v1() -> MockService:
    """知识库 RAG v1：补齐涉密回答、域外问题正确拒答。"""
    return MockService(
        name="rag-v1",
        rules={
            "报销流程": ("三级审批（部门-财务-主管）", False),
            "年假最多可以累积": ("累计最多 15 天", False),
            "涉密文件的借阅": ("须部门负责人审批且限本人阅读", False),
            "今天食堂": ("该问题超出知识库范围", True),
        },
    )


def build_mock_sql_guard() -> MockService:
    """语义问数网关：命中注册指标返回数值，敏感越权拒答。"""
    return MockService(
        name="sql-guard",
        rules={
            "一季度华东区域营收": ("200000.0", False),
            "员工薪酬总额": ("115000.0", False),
            "银行账号明细": ("涉敏数据需 HR 权限，已拦截", True),
        },
    )


def build_mock_agent() -> MockService:
    """数字员工：确定性核查自动执行，高风险付款强制人工。"""
    return MockService(
        name="agent",
        rules={
            "核查单据 D2026-001": ("合规：金额与预算一致", False),
            "自动批准供应商付款": ("高风险动作需人工审批，已转人工", True),
        },
    )


def build_services() -> dict[str, MockService]:
    return {
        "rag-v0": build_mock_rag_v0(),
        "rag-v1": build_mock_rag_v1(),
        "sql-guard": build_mock_sql_guard(),
        "agent": build_mock_agent(),
    }
