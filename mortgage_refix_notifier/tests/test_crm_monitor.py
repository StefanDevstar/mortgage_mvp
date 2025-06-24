# tests/test_crm_monitor.py

from app.agents.crm_monitor import monitor_crm_for_refix
from app.config import CRM_DATA_PATH

def test_crm_monitor():
    alerts = monitor_crm_for_refix(CRM_DATA_PATH)
    assert isinstance(alerts, list)
    assert all("email" in alert for alert in alerts)
