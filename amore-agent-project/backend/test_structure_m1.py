import sys
import os

# Adjust path to import from scripts-model1 (which mimics model_1 package)
current_dir = os.path.dirname(os.path.abspath(__file__))
# scripts-model1 is treated as a package, so we append the current dir (backend) 
# so 'scripts-model1' can be imported. 
# BUT, the original imports in scripts-model1 might be relative (e.g. from .config import ...)
# which works if scripts-model1 is a package.
sys.path.append(current_dir)

# We need to temporarily rename 'scripts-model1' to 'model_1' or adjust imports?
# Actually, the user named the folder 'scripts-model1', but the code inside likely expects
# to be part of a package or uses relative imports. 
# If I import `scripts-model1.retriever`, it should work if the folder has __init__.py.
# However, the code in schemas.py or retriever.py might use `from .config import...` 
# which works fine if imported as a module.

try:
    from importlib import import_module
    # Importing as if the folder name is the package name
    retriever_module = import_module("scripts-model1.retriever")
    get_retriever = retriever_module.get_retriever

    print("Initializing Model-1 from 'scripts-model1'...")
    retriever = get_retriever()
    
    query = "라네즈 크림스킨"
    print(f"Testing Query: {query}")
    results = retriever.retrieve(query)
    
    if len(results) > 0:
        print("SUCCESS: Retrieval returned results.")
        print(f"Top-1: {results[0].product_name}")
    else:
        print("WARNING: No results found.")

except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
