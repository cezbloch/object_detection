import logging
import time
from functools import wraps
from typing import Dict

import torch

logging.basicConfig(
    filename="profiling.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TimedLayer(torch.nn.Module):
    """A wrapper class to measure the time taken by a layer in milliseconds"""

    def __init__(self, module: torch.nn.Module, indent: str = "\t"):
        super().__init__()
        assert isinstance(module, torch.nn.Module)
        assert not isinstance(module, TimedLayer)
        self._module = module
        self._module_name = module.__class__.__name__
        self._total_time_ms = 0.0
        self._indent = indent

    def forward(self, *args, **kwargs):
        with torch.no_grad():
            start_time = time.time()
            x = self._module(*args, **kwargs)
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            end_time = time.time()
            self._total_time_ms = (end_time - start_time) * 1000
            logger.info(
                f"{self._indent}Layer {self._module_name}: {self._total_time_ms:.6f} ms."
            )
            return x

    def __len__(self):
        return len(self._module)

    def __iter__(self):
        return iter(self._module)

    def __getattr__(self, attribute_name):
        """
        Delegate all other attribute access to the wrapped layer.

        NOTE: __getattr__ is called when the attribute is not found in the object's dictionary.
        """
        try:
            return super().__getattr__(attribute_name)
        except AttributeError:
            return getattr(self._module, attribute_name)

    def get_timings(self) -> Dict:
        timings = {
            "module_name": self._module_name,
            "total_time": self._total_time_ms,
            "sub_modules": [],
        }

        children = timings["sub_modules"]

        for _, child in self._module.named_children():
            if isinstance(child, TimedLayer):
                children.append(child.get_timings())

        return timings


def wrap_model_layers(model, indent="\t") -> TimedLayer:
    """Wrap all torch Module layers of a given model with TimedLayer, to print each layer execution time."""
    assert isinstance(model, torch.nn.Module)
    assert not isinstance(model, TimedLayer)

    print(f"{indent}{model.__class__.__name__}")

    for attribute_name, child in model.named_children():
        wrap_model_layers(child, indent + "\t")
        wrapped_child = TimedLayer(child, indent)
        setattr(model, attribute_name, wrapped_child)

    return TimedLayer(model, indent)


def profile_function(f):
    """Decorator to profile function calls. Prints the time taken by the function in milliseconds."""

    @wraps(f)
    def wrap(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        elapsed_ms = (te - ts) * 1000
        logger.info(f"Function '{f.__name__}' executed in {elapsed_ms:.4f} ms.")
        return result

    return wrap
