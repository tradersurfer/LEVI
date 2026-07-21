"""Read-only dashboard projections for LEVI."""

from .service import DashboardService
from .models import DashboardSummary
from .routes import build_dashboard_router

__all__ = ["DashboardService", "DashboardSummary", "build_dashboard_router"]
