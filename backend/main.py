import importlib.machinery
import os
import sys


LOCAL_LIBS = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".pythonlibs")
if os.path.isdir(LOCAL_LIBS):
    sys.path.insert(0, LOCAL_LIBS)

    pydantic_core_dir = os.path.join(LOCAL_LIBS, "pydantic_core")
    compiled_core_files = [
        os.path.join(pydantic_core_dir, name)
        for name in os.listdir(pydantic_core_dir)
        if name.startswith("_pydantic_core") and name.endswith(".pyd")
    ] if os.path.isdir(pydantic_core_dir) else []
    expected_core_files = [
        os.path.join(pydantic_core_dir, f"_pydantic_core{suffix}")
        for suffix in importlib.machinery.EXTENSION_SUFFIXES
    ]
    if compiled_core_files and not any(os.path.exists(path) for path in expected_core_files):
        installed_tags = ", ".join(os.path.basename(path) for path in compiled_core_files)
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        raise SystemExit(
            "The backend dependencies in .pythonlibs were installed for a different "
            f"Python version than the one running now.\n\n"
            f"Current Python: {sys.executable} ({python_version})\n"
            f"Installed native dependency: {installed_tags}\n\n"
            "Start the backend with the matching Python instead:\n"
            "  py -3.13 main.py\n\n"
            "Or rebuild .pythonlibs for your current Python version:\n"
            "  python -m pip install -r requirements.txt -t .pythonlibs --upgrade"
        )

from app.main import app  # noqa: E402


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
