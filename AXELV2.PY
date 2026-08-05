"""AXEL v2 - thin wrapper around the canonical Streamlit app in axel.py.

Run with:  streamlit run AXELV2.PY
"""

import os
import runpy

_HERE = os.path.dirname(os.path.abspath(__file__))
runpy.run_path(os.path.join(_HERE, "axel.py"), run_name="__main__")
