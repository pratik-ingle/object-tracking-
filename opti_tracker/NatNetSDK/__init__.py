"""NatNetSDK package initializer.

Exports the primary client class and re-exports the data description and
frame data modules. Also provides compatibility aliases so intra-package
absolute imports like `import DataDescriptions` continue to work when the
package is imported.
"""

import sys as _sys

# Re-export submodules for convenient access
from . import DataDescriptions as DataDescriptions  # noqa: F401
from . import MoCapData as MoCapData  # noqa: F401

# Backwards-compatibility: allow bare imports used inside the SDK sources
_sys.modules.setdefault("DataDescriptions", DataDescriptions)
_sys.modules.setdefault("MoCapData", MoCapData)

# Export primary client class (after aliases are registered)
from .NatNetClient import NatNetClient  # noqa: F401,E402

__all__ = [
    "NatNetClient",
    "DataDescriptions",
    "MoCapData",
]


