import pkgutil

for finder, name, ispkg in pkgutil.iter_modules():
    # not include in .venv/
    if "ai-service\\app" in finder.path:
        print(finder.path, name, ispkg)
