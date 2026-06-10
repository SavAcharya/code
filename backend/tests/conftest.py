import os, sys
# Make backend/ importable (config.py, llm/ are top-level there)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
