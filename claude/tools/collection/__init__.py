"""Collection intelligence services - Unified Intelligence Framework.

This package provides the base infrastructure for all intelligence collection
services (Trello, Grafana, Dynatrace, etc.) with unified interfaces for:
- Data freshness reporting
- Staleness detection
- Raw querying
- Refresh operations

Sprint: SPRINT-UFC-001 (Unified Intelligence Framework)
Phase: 265
"""

from claude.tools.collection.base_intelligence_service import (
    BaseIntelligenceService,
    QueryResult,
    FreshnessInfo,
)
from claude.tools.collection.otc_intelligence_service import OTCIntelligenceService
from claude.tools.collection.otc_query_templates import (
    execute_template,
    describe_templates,
    TEMPLATES,
)

__all__ = [
    "BaseIntelligenceService",
    "QueryResult",
    "FreshnessInfo",
    "OTCIntelligenceService",
    "execute_template",
    "describe_templates",
    "TEMPLATES",
]
