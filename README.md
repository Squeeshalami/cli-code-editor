# Squeeshalami Terminal Text Editor

A modern, terminal-based text editor built with Python and Textual, featuring a clean interface, syntax highlighting, and intuitive file management.

## ✨ Features

### 📁 **File Management**
- **Directory Tree Navigation** - Browse files and folders in an intuitive tree view
- **Create New Files** - `Ctrl+N` to create files in any directory
- **Create New Folders** - `Ctrl+F` to create folders anywhere in your project
- **Delete Files/Folders** - `Delete` key with confirmation dialog for safe deletion
- **Smart File Detection** - Automatic syntax highlighting based on file extensions
- **Global Command Access** - Optional `stext` command for system-wide editor access

### ⌨️ **Keyboard Shortcuts**
- `Ctrl+S` - Save current file
- `Ctrl+N` - Create new file
- `Ctrl+F` - Create new folder  
- `Ctrl+Q` - Quit application
- `Delete` - Delete selected file/folder
- `Enter` - Confirm dialogs
- `Escape` - Cancel dialogs

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Either `pip` or `uv` (recommended)

### Installation

Choose your preferred method:

#### Option A: Using UV (Recommended) 🚀

1. **Install UV** (if not already installed)
    https://docs.astral.sh/uv/getting-started/installation/

2. **Clone the repository**
   ```bash
   git clone https://github.com/Squeeshalami/cli-code-editor.git
   cd cli-code-editor
   ```

3. **Sync dependencies from pyproject.toml**
   ```bash
   uv sync
   ```

4. **Run the editor**
   ```bash
   uv run python app.py
   ```

#### Option B: Using pip (Traditional)

1. **Clone the repository**
   ```bash
   git clone https://github.com/Squeeshalami/cli-code-editor.git
   cd cli-code-editor
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install textual
   ```

### Global Command Setup (Linux/macOS) 🌟

For even easier access, you can set up the `stext` command to run the editor from anywhere:

1. **Copy the stext script to your PATH**
   ```bash
   # Make the script executable
   chmod +x stext
   
   # Copy to a directory in your PATH (choose one):
   sudo cp stext /usr/local/bin/     # System-wide installation
   # OR
   cp stext ~/.local/bin/            # User-only installation
   ```

2. **Update the script with your project path**
   ```bash
   # Edit the script to point to your installation
   nano ~/.local/bin/stext  # or /usr/local/bin/stext
   
   # Change this line in the script:
   PROJECT_DIR=PATH/TO/PROJECT/DIR
   # To your actual path, for example:
   PROJECT_DIR=/home/yourusername/cli-code-editor
   ```

3. **Reload your shell or restart terminal**
   ```bash
   source ~/.bashrc  # or source ~/.zshrc
   ```

**Now you can use `stext` from anywhere!**

#### Benefits of stext Command:
- 🚀 **Launch from anywhere** - No need to navigate to the editor directory
- 📁 **Automatic directory detection** - Always opens in your current working directory  
- 🎯 **Quick file editing** - `stext filename.py` loads files instantly
- 🔧 **UV integration** - Uses UV for fast, reliable execution

### Usage

#### With stext Command (Recommended after setup)

**Open current directory**
```bash
stext
```
*Opens the editor in the current working directory*

**Open specific file in current directory**
```bash
stext filename.py
```
*Opens the editor in the current directory and loads the specified file*

**Open specific directory**
```bash
stext -d /path/to/dir
stext --directory /path/to/dir
```
*Opens the editor in the specified directory instead of the current directory*

**Open specific directory with file**
```bash
stext -d /path/to/dir filename.py
stext --directory /path/to/dir filename.py
```
*Opens the editor in the specified directory and loads the specified file*

**Use from any directory**
```bash
cd /any/project/directory
stext                    # Edit files in this directory
stext main.py           # Edit main.py in this directory
stext -d ~/other-project # Edit files in ~/other-project
stext -d ~/docs README.md # Edit README.md in ~/docs
```

#### stext Command Options

| Option | Description | Example |
|--------|-------------|---------|
| (none) | Open current directory | `stext` |
| `filename` | Open file in current directory | `stext app.py` |
| `-d DIR` | Open specific directory | `stext -d /path/to/project` |
| `--directory DIR` | Open specific directory (long form) | `stext --directory /path/to/project` |
| `-d DIR filename` | Open file in specific directory | `stext -d ~/project main.py` |

#### With UV (if you used Option A)

**Basic Usage**
```bash
uv run python app.py
```
*Opens the editor in the current directory*

**Open Specific Directory**
```bash
uv run python app.py /path/to/your/project
```
*Opens the editor with the specified directory*

**Open Specific File**
```bash
uv run python app.py /path/to/directory filename.py
```
*Opens the editor in the directory and loads the specified file*

#### With pip/venv (if you used Option B)

**Basic Usage**
```bash
python app.py
```
*Opens the editor in the current directory*

**Open Specific Directory**
```bash
python app.py /path/to/your/project
```
*Opens the editor with the specified directory*

**Open Specific File**
```bash
python app.py /path/to/directory filename.py
```
*Opens the editor in the directory and loads the specified file*

## 🎯 Supported File Types

The editor provides syntax highlighting for:

| Language | Extensions |
|----------|-----------|
| Python | `.py` |
| JavaScript | `.js`, `.jsx` |
| TypeScript | `.ts`, `.tsx` |
| HTML | `.html` |
| CSS | `.css` |
| Java | `.java` |
| C/C++ | `.c`, `.cpp` |
| C# | `.cs`, `.csproj` |
| Go | `.go` |
| Lua | `.lua` |
| Swift | `.swift` |
| Kotlin | `.kt` |
| Ruby | `.rb` |
| PHP | `.php` |
| Rust | `.rs` |
| JSON | `.json`, `.jsonl` |
| Markdown | `.md` |
| YAML | `.yaml`, `.yml` |
| TOML | `.toml` |
| XML | `.xml` |
| CSV | `.csv` |
| Bash/Shell | `.sh` |
| PowerShell | `.ps1`, `.psm1` |
| Batch | `.bat` |
| GDScript | `.gd` |
| Godot | `.godot` |
| Git Config | `.gitignore`, `.gitconfig`, `.gitmodules` |
| Lock Files | `.lock` |

*Unsupported file types will open with plain text editing.*