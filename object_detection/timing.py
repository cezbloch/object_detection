import time
from functools import wraps

import torch


class TimedLayer(torch.nn.Module):
    """A wrapper class to measure the time taken by a layer in milliseconds"""

    def __init__(self, layer: torch.nn.Module, indent: str):
        super(TimedLayer, self).__init__()
        self.layer = layer
        self._total_time = 0.0
        self.indent = indent

    def forward(self, *args, **kwargs):
        start_time = time.time()
        x = self.layer(*args, **kwargs)
        torch.cuda.synchronize()  # Synchronize if using GPU
        end_time = time.time()
        self._total_time = (end_time - start_time) * 1000
        print(
            f"{self.indent}Layer {self.layer.__class__.__name__}: {self._total_time:.6f} ms"
        )
        return x

    def postprocess(self, *args, **kwargs):
        return self.layer.postprocess(*args, **kwargs)

    def __len__(self):
        return len(self.layer)

    def __iter__(self):
        return iter(self.layer)

    def __next__(self):
        return next(iter(self.layer))

    # def __getattribute__(self, name):
    #     print(f"Intercepted access to: {name}")
    #     try:
    #         print(f"Trying to get attribute: {name}")
    #         return TimedLayer().__getattribute__(name)
    #     except AttributeError as e:
    #         return self.layer.__getattribute__(name)
    #     except Exception as e:
    #         print(f"Error: {e}")
    #         def method(*args, **kwargs):
    #             print(f"Handling non-existent method: {name}")
    #             return f"Handled method: {name}"
    #         return method

    def get_time(self):
        return self._total_time


def wrap_model_layers(model, indent="\t") -> None:
    """Wrap all torch Module layers of a given model with TimedLayer, to print each layer execution time."""
    attributes = dir(model)
    for a in attributes:
        attr = getattr(model, a)
        if isinstance(attr, torch.nn.Module):
            setattr(model, a, TimedLayer(attr, indent))
            wrap_model_layers(attr, indent + "\t")


def profile_function(f):
    """decorator to profile function calls. Prints the time taken by the function in milliseconds"""

    @wraps(f)
    def wrap(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        elapsed_ms = (te - ts) * 1000
        print(f"Function '{f.__name__}' executed in {elapsed_ms:.4f} ms.")
        return result

    return wrap
