from __future__ import annotations

import datetime as dt
import threading
from typing import Callable, Dict

from fastapi import HTTPException


process_state_lock = threading.Lock()
process_state = {
    "processing": False,
    "current_action": None,
    "last_run": None,
    "last_result": None,
}


def get_process_status () -> Dict[str, object] :
    """
    Return the current process state snapshot.
    """
    with process_state_lock :
        return {
            "processing": process_state["processing"],
            "current_action": process_state["current_action"],
            "last_run": process_state["last_run"],
            "last_result": process_state["last_result"],
        }


def run_tracked_job (action_name : str, runner : Callable[[], Dict[str, object]]) -> Dict[str, object] :
    """
    Execute a background-like job while tracking status in memory.
    """
    with process_state_lock :
        if process_state["processing"] :
            raise HTTPException(status_code=409, detail="Processing already in progress")
        
        process_state["processing"] = True
        process_state["current_action"] = action_name

    try :
        result = runner()
        payload = {"action": action_name, **result}
        
        with process_state_lock :
            process_state["processing"] = False
            process_state["current_action"] = None
            process_state["last_run"] = dt.datetime.utcnow().isoformat() + "Z"
            process_state["last_result"] = payload
        
        return payload
    
    except Exception as exc :
        with process_state_lock :
            process_state["processing"] = False
            process_state["current_action"] = None
        
        raise HTTPException(status_code=500, detail=str(exc)) from exc
