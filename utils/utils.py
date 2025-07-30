import inspect
from textual.app import App
from textual.theme import Theme
import utils.themes  

def register_custom_themes(app: App) -> None:
    """Dynamically finds and registers all Theme instances from the themes module."""
    custom_themes = []
    count = 0
    for name, obj in inspect.getmembers(utils.themes):
        if isinstance(obj, Theme):
            custom_themes.append(obj)
    for theme in custom_themes:
        app.register_theme(theme)
        count += 1
    print(f"Registered {count} custom themes")


LANGUAGE_MAP = {
    ".py":   "python",
    ".js":   "javascript",
    ".jsx":  "javascriptreact",
    ".ts":   "typescript",
    ".tsx":  "typescriptreact",
    ".html": "html",
    ".css":  "css",
    ".java": "java",
    ".c":    "c",
    ".cpp":  "cpp",
    ".cs":   "csharp",
    ".csproj": "xml",
    ".snl":  "snl",
    ".go":   "go",
    ".lua":  "lua",
    ".swift": "swift",
    ".kt":   "kotlin",
    ".rb":   "ruby",
    ".php":  "php",
    ".json": "json",
    ".md":   "markdown",
    ".sh":   "bash",
    ".yaml": "yaml",
    ".yml":  "yaml",
    ".toml": "toml",
    ".xml":  "xml",
    ".csv":  "csv",
    ".jsonl": "jsonl",
    ".gd":   "gdscript",
    ".godot": "godot",
    ".lock": "lock",
    ".rs":   "rust",
    ".ps1":  "powershell",
    ".psm1": "powershell",
    ".bat":  "batch",
    ".gitignore": "gitignore",
    ".gitconfig": "gitconfig",
    ".gitmodules": "gitmodules",
}