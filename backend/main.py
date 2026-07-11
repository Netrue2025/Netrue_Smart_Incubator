from pathlib import Path
import importlib.machinery
import sys


LOCAL_LIBS = Path(__file__).resolve().parent / ".pythonlibs"
if LOCAL_LIBS.exists():
    sys.path.insert(0, str(LOCAL_LIBS))

    pydantic_core_dir = LOCAL_LIBS / "pydantic_core"
    compiled_core_files = list(pydantic_core_dir.glob("_pydantic_core*.pyd"))
    expected_core_files = [
        pydantic_core_dir / f"_pydantic_core{suffix}"
        for suffix in importlib.machinery.EXTENSION_SUFFIXES
    ]
    if compiled_core_files and not any(path.exists() for path in expected_core_files):
        installed_tags = ", ".join(path.name for path in compiled_core_files)
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
