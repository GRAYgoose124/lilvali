from dataclasses import dataclass, field

from ..errors import BindingError


@dataclass
class GenericBinding:
    """Represents a Generic type binding state."""

    ty: type = None
    instances: list = field(default_factory=list)

    @property
    def is_bound(self):
        """True if the GenericBinding is unbound"""
        return self.ty is not None

    @property
    def none_bound(self):
        return len(self.instances) == 0

    @property
    def can_bind_generic(self):
        """True if the GenericBinding can bind to a new arg."""
        return self.is_bound or self.none_bound

    def can_new_arg_bind(self, arg):
        """True if a given arg can be bound to the current GenericBinding context."""
        return not self.is_bound or self.ty == type(arg)

    def try_bind_new_arg(self, arg):
        if self.can_new_arg_bind(arg):
            self.ty = type(arg)
            self.instances.append(arg)
        else:
            raise BindingError(
                f"Generic bound to different types: {self.ty}, but arg is {type(arg)}"
            )


class GenericBindings(dict):
    def __init__(self, generics):
        super().__init__({G: GenericBinding() for G in generics})

    def try_bind_new_arg(self, ann, arg):
        self.setdefault(ann, GenericBinding()).try_bind_new_arg(arg)
