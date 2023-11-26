from dataclasses import dataclass
from typing import Any


@dataclass
class BindCheckerConfig(dict):
    strict: bool = True
    implied_lambdas: bool = False
    ret_validation: bool = True
    disabled: bool = False

    use_custom_validators: bool = True

    performance: bool = False
    no_list_check: bool = False
    no_tuple_check: bool = False
    no_dict_check: bool = False

    ignore_generics: bool = False

    def __getitem__(self, __key: Any) -> Any:
        if __key not in self:
            return None
        return super().__getitem__(__key)
