from typing import Optional

from core.model import FuncType


def build_metadata(
    func_type: FuncType,
    name: str,
    version: str,
    description: str,
    usage: Optional[list[str]] = None,
    options: Optional[list[dict[str, str]]] = None,
    example: Optional[list[dict[str, str]]] = None,
    can_be_disabled: bool = True,
    default_enable: bool = True,
    hidden: bool = False,
    maintain: bool = False,
):
    if usage is None:
        usage = []
    else:
        usage = [s.replace("<", "&lt;").replace(">", "&gt;") for s in usage]
    if options is None:
        options = []
    else:
        options = [
            {k: v.replace("<", "&lt;").replace(">", "&gt;") for k, v in d.items()}
            for d in options
        ]
    if example is None:
        example = []
    else:
        example = [
            {k: v.replace("<", "&lt;").replace(">", "&gt;") for k, v in d.items()}
            for d in example
        ]
    return {
        "func_type": func_type,
        "name": name,
        "version": version,
        "description": description,
        "usage": usage,
        "options": options,
        "example": example,
        "can_be_disabled": can_be_disabled,
        "default_enable": default_enable,
        "hidden": hidden,
        "maintain": maintain,
    }
