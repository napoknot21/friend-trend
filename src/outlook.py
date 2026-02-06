from __future__ import annotations

import re
import datetime as dt
import win32com.client as win32 # type: ignore

from typing import Optional, List, Dict, Any, Tuple

from src.utils import str_to_date, date_to_str
from src.config.parameters import EMAILBOX_SUFFIX


def get_mapi_namespace (outlook : Optional[win32.Dispatch] = None) :
    """
    Return the MAPI namespace (Outlook session).
    """
    outlook = win32.Dispatch("Outlook.Application") if outlook is None else outlook
    
    namespace = outlook.GetNamespace("MAPI")
    namespace.Logon()
    
    return namespace


def get_mailbox_by_suffix (
        
        namespace : Optional[Any] = None,
        emailbox_suffix : Optional[str] = None
        
    ) -> Optional[Any] :
    """
    Return the mailbox whose name ends with `mailbox_suffix`.

    :param namespace: Description
    :type namespace: Optional[Any]
    :param emailbox_suffix: Description
    :type emailbox_suffix: Optional[str]
    :return: Description
    :rtype: Any | None
    """
    namespace = get_mapi_namespace() if namespace is None else namespace
    emailbox_suffix = EMAILBOX_SUFFIX if emailbox_suffix is None else emailbox_suffix

    print("\n[+] Available Outlook stores/mailboxes: ")

    for mailbox in namespace.Folders :

        print(f"\n\t - {mailbox.Name}")
        
        if mailbox.Name.lower().endswith(emailbox_suffix.lower()) :

            print(f"\n[+] Using mailbox: {mailbox.Name}")
            return mailbox

    print(f"\n[-] No mailbox found ending with '{emailbox_suffix}'")
    
    return None


def get_folder_by_path (
        
        mailbox : Optional[Any] = None,
        folder_path : Optional[List[str]] = ["Inbox"],

    ) :
    """
    Docstring for get_folder_by_path
    
    :param mailbox: Description
    :type mailbox: Optional[Any]
    :param folder_path: Description
    :type folder_path: Optional[List[str]]
    """
    if folder_path is None or len(folder_path) == 0 :
        return None

    mailbox = get_mailbox_by_suffix() if mailbox is None else mailbox
    folder = mailbox
    
    for name in folder_path :
        
        try :
            folder = folder.Folders.Item(name)

        except :
            return None
        
    return folder


def read_emails_from_folder (
    
        folder : Optional[Any] = None,
        
        start_date : Optional[str | dt.datetime | dt.date] = None,
        end_date   : Optional[str | dt.datetime | dt.date] = None,
        
        max_items  : int = 300,
        max_scanned : int = 50000,   # stop safety
        
    ) -> List[Dict[str, Any]] :

    folder = get_folder_by_path() if folder is None else folder
    
    if folder is None :
        raise ValueError("Folder is None. Check get_folder_by_path() / folder name.")

    start_dt = str_to_date(start_date)
    end_dt   = str_to_date(end_date)

    items = folder.Items
    items.Sort("[ReceivedTime]", True)  # newest first

    results: List[Dict[str, Any]] = []
    
    kept = 0
    scanned = 0

    for msg in items :
        
        if scanned >= max_scanned :
            print(scanned)
            print(f"[!] STOP: max_scanned reached ({max_scanned}).")
            break

        scanned += 1

        try :

            received = msg.ReceivedTime

            received = dt.datetime(
                received.year, received.month, received.day,
                received.hour, received.minute, received.second
            )

            # If we sort newest -> oldest:
            # once we are older than start_dt, everything after is older -> break
            if start_dt and received.date() <= start_dt :
                # break is correct because received will only decrease afterwards
                break

            if end_dt and received.date() > end_dt :
                # too recent -> skip
                continue
            
            print(received)
            results.append(
            
                {
                    "received_time": received,
                    "subject": str(getattr(msg, "Subject", "") or ""),
                    "sender": str(getattr(msg, "SenderEmailAddress", "") or ""),
                    "body": str(getattr(msg, "Body", "") or ""),
                }
            
            )

            kept += 1
            
            if kept >= max_items :
                break

        except Exception as e :
            continue

    return results



