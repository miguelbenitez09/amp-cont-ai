import os

plugin_dirs = [
    "plugins/portops/datasets",
    "plugins/portops/features",
    "plugins/portops/models",
    "plugins/portops/tools",
    "plugins/portops/rag",
    "plugins/portops/regulations"
]

for d in plugin_dirs:
    os.makedirs(d, exist_ok=True)
    init_file = os.path.join(d, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w", encoding="utf-8") as f:
            f.write("# PortOps domain sub-package\n")

manifest_path = "plugins/portops/plugin.yaml"
with open(manifest_path, "w", encoding="utf-8") as f:
    f.write("""name: "portops"
version: "1.0.0"
description: "Panama Maritime & Port Operations Domain Intelligence Plugin"
author: "Desarrollado v1.0.0 Miguel Benitez"
license: "GNU GPL-3.0"
jurisdiction: "Republic of Panama - AMP / ANA / ACP"
components:
  - datasets
  - features
  - models
  - tools
  - rag
  - regulations
""")

print("PortOps plugin scaffolding complete.")
