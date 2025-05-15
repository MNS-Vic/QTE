_norm = None
import numpy

if(numpy.__version__.startswith('1.')):
    from numpy.lib import issubsctype
else:
    from numpy import issubdtype as issubsctype

def load_norm():
    global _norm
    if _norm is not None:
        return _norm
    try:
        from scipy.stats import norm
        _norm = norm
        return norm
    except ModuleNotFoundError as e:
        from gm.utils import gmsdklogger
        gmsdklogger.warn("未安装 scipy 库或 scipy 库不支持该版本 Python 解释器, 请手动安装 scipy 库或使用其他 Python 版本 SDK")
        raise e
