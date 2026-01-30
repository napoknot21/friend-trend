from __future__ import annotations

import polars as pl
import win32com.client as win32

from typing import Optional, Any, List, Dict, Tuple
from src.config.parameters import EMAILBOX_SUFFIX


def get_mapi_namespace (outlook : Optional[win32.Dispatch] = None) :
    """
    Return the MAPI namespace (Outlook session).
    """
    outlook = win32.Dispatch("Outlook.Application")  if outlook is None else outlook
    
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


def read_emails (
        
        inbox: Any,

        subject_contains : str,
        body_contains : str,
        
        sender_domain : Optional[str] = None,
        
        max_items : int = 3000,

    ) -> Optional[Any] :
    """
    Docstring for read_emails
    
    :param inbox: Description
    :type inbox: Any
    :param subject_contains: Description
    :type subject_contains: str
    :param body_contains: Description
    :type body_contains: str
    :param sender_domain: Description
    :type sender_domain: Optional[str]
    :param fundation: Description
    :type fundation: str
    :param max_items: Description
    :type max_items: int
    :return: Description
    :rtype: Any | None
    """

    messages = inbox.Items
    messages.Sort("[ReceivedTime]", True)

    inspected = 0

    for message in messages :

        try :

            inspected += 1
            
            if inspected > max_items :
                
                print(f"\n[-] Process stopped after {max_items} items.")
                break

        except :

            print("Helo world")

    return
