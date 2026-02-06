from __future__ import annotations

import datetime as dt
from typing import Optional, List, Dict, Any

import win32com.client as win32  # type: ignore
import pythoncom  # type: ignore

from src.utils import str_to_date
from src.config.parameters import EMAILBOX_SUFFIX


MAILITEM_CLASS = 43


def get_mapi_namespace (outlook: Optional[win32.Dispatch] = None) :
    """
    Docstring for get_mapi_namespace
    
    :param outlook: Description
    :type outlook: Optional[win32.Dispatch]
    """
    outlook = win32.Dispatch("Outlook.Application") if outlook is None else outlook

    namespace = outlook.GetNamespace("MAPI")
    namespace.Logon()

    return namespace


def get_mailbox_by_suffix(namespace: Optional[Any] = None, emailbox_suffix: Optional[str] = None) -> Optional[Any] :
    """
    Docstring for get_mailbox_by_suffix
    
    :param namespace: Description
    :type namespace: Optional[Any]
    :param emailbox_suffix: Description
    :type emailbox_suffix: Optional[str]
    :return: Description
    :rtype: Any | None
    """
    namespace = get_mapi_namespace() if namespace is None else namespace
    emailbox_suffix = EMAILBOX_SUFFIX if emailbox_suffix is None else emailbox_suffix

    for mailbox in namespace.Folders:
        
        if mailbox.Name.lower().endswith(emailbox_suffix.lower()):
            return mailbox

    return None


def get_folder_by_path (mailbox: Optional[Any] = None, folder_path: Optional[List[str]] = None) :
    """
    Docstring for get_folder_by_path
    
    :param mailbox: Description
    :type mailbox: Optional[Any]
    :param folder_path: Description
    :type folder_path: Optional[List[str]]
    """
    if not folder_path :
        folder_path = ["Inbox"]

    mailbox = get_mailbox_by_suffix() if mailbox is None else mailbox
    
    if mailbox is None:
        return None

    folder = mailbox

    for name in folder_path :

        try:
            folder = folder.Folders.Item(name)
        
        except Exception :
            return None
        
    return folder


def _safe_str(x: Any) -> str :
    """
    Docstring for _safe_str
    
    :param x: Description
    :type x: Any
    :return: Description
    :rtype: str
    """
    try :
        return str(x or "")
    
    except Exception :
        return ""


def _get_headers(msg: Any) -> str :
    """
    Optional debug: raw transport headers.
    """
    PR_TRANSPORT_MESSAGE_HEADERS = "http://schemas.microsoft.com/mapi/proptag/0x007D001E"
    
    try :
        return _safe_str(msg.PropertyAccessor.GetProperty(PR_TRANSPORT_MESSAGE_HEADERS))
    
    except Exception :
        return ""


def read_emails_from_folder (
        
        folder: Optional[Any] = None,
        start_date: Optional[str | dt.datetime | dt.date] = None,
        end_date: Optional[str | dt.datetime | dt.date] = None,
        max_items: int = 3000,
        max_scanned: int = 50000,
        folder_path: Optional[List[str]] = None,
        include_headers: bool = False,
    
    ) -> List[Dict[str, Any]]:

    pythoncom.CoInitialize()

    folder = get_folder_by_path(folder_path=folder_path) if folder is None else folder
    
    if folder is None :
        raise ValueError("Folder is None. Check get_folder_by_path() / folder name.")

    start_dt = str_to_date(start_date)  # suppose returns dt.date|None
    end_dt = str_to_date(end_date)

    items = folder.Items
    items.Sort("[ReceivedTime]", True)  # newest first

    results: List[Dict[str, Any]] = []
    kept = 0
    scanned = 0

    for msg in items :

        if scanned >= max_scanned:
        
            print(f"[!] STOP: max_scanned reached ({max_scanned}).")
            break
        
        scanned += 1

        try :
            
            # Filter only MailItem
            if getattr(msg, "Class", None) != MAILITEM_CLASS:
                continue

            received = msg.ReceivedTime
            received = dt.datetime(
                received.year, received.month, received.day,
                received.hour, received.minute, received.second
            )

            # With newest->oldest ordering:
            if start_dt and received.date() <= start_dt:
                break  # everything after is older

            if end_dt and received.date() > end_dt:
                continue  # too recent

            body_text = _safe_str(getattr(msg, "Body", ""))
            body_html = _safe_str(getattr(msg, "HTMLBody", ""))

            row = {
                "received_time": received,
                "subject": _safe_str(getattr(msg, "Subject", "")),
                "sender": _safe_str(getattr(msg, "SenderEmailAddress", "")),
                "body": body_text,
                "html_body": body_html,
            }

            if include_headers:
                row["headers"] = _get_headers(msg)

            results.append(row)
            kept += 1
            
            if kept >= max_items :
                break

        except Exception as e :

            # Log minimal info to debug instead of silent skip
            try:
                subj = _safe_str(getattr(msg, "Subject", ""))
            
            except Exception :
                subj = ""
                
            print(f"[!] Error reading message (subject={subj!r}): {e}")
            continue

    return results
