import numpy as np


def serialize_model_output(obj):
    """Serialize complex objects for JSON response."""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(
        obj,
        (
            np.integer,
            np.int_,
            np.intc,
            np.intp,
            np.int8,
            np.int16,
            np.int32,
            np.int64,
        ),
    ):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    elif hasattr(obj, "__dict__"):
        return {str(k): serialize_model_output(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_model_output(i) for i in obj]
    elif isinstance(obj, dict):
        return {str(k): serialize_model_output(v) for k, v in obj.items()}
    else:
        return obj
