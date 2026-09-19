# test_approval_gate.py
import os
import pytest
from code_implementation import ApprovalGatedSummaryEngine

def test_engine_skips_compilation_if_not_approved():
    """Confirms the generator returns None and creates no files for unapproved tasks."""
    engine = ApprovalGatedSummaryEngine(workspace_root="/mock/dir")
    
    unapproved_task = {
        "id": "TS-016",
        "status": "Active", # Task is still being worked on
        "component": "Route Controller"
    }
    
    result = engine.process_task_state_change(unapproved_task, ["main.py"])
    assert result is None

def test_engine_executes_only_when_status_is_approved(tmp_path):
    """Confirms that the file is generated when the status matches APPROVED."""
    engine = ApprovalGatedSummaryEngine(workspace_root=str(tmp_path))
    
    approved_task = {
        "id": "TS-015",
        "status": "Approved", # Gate condition met
        "component": "State Listener Hook",
        "phase": "ENGINEERING",
        "verification_metric": "Callback unit tests pass",
        "approval_note": "Codebase matches functional specifications."
    }
    
    result = engine.process_task_state_change(approved_task, ["state_listener.py"])
    
    assert result is not None
    assert "SIGNED OFF / APPROVED" in result
    assert "TS-015" in result
    
    # Confirm the physical summary report document was written to the directory
    expected_file = tmp_path / ".agents" / "reports" / "summary_TS-015.md"
    assert expected_file.exists() is True
