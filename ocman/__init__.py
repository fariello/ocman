import sys
from . import cli

# Forward all attribute lookups and modifications to the underlying cli module.
# This ensures that test mocks rebinding global variables (like OCMAN_CONFIG_PATH,
# OPENCODE_DB_PATH, etc.) are correctly reflected inside ocman/cli.py.
def __getattr__(name):
    try:
        return getattr(cli, name)
    except AttributeError:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

def __setattr__(name, value):
    # Avoid infinite recursion during module setup
    if name == 'cli':
        super(module, sys.modules[__name__]).__setattr__(name, value)
    else:
        setattr(cli, name, value)

# Set the module class so __setattr__ is called on the module level
class ModuleWrapper(sys.modules[__name__].__class__):
    def __setattr__(self, name, value):
        if name == 'cli':
            super().__setattr__(name, value)
        else:
            setattr(cli, name, value)

sys.modules[__name__].__class__ = ModuleWrapper

# Support "from ocman import *" by defining __all__
__all__ = [name for name in dir(cli) if not name.startswith('__')]
