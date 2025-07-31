from __future__ import annotations
from pathlib import Path
import sys
import shutil
import json

from textual.app import App, ComposeResult
from textual.widgets import DirectoryTree, TextArea, Footer, Header, TabbedContent, TabPane
from textual.events import Key, Resize
from textual.css.query import NoMatches
from textual import work

from utils.utils import LANGUAGE_MAP, TEXTAREA_THEME_MAP, register_custom_themes
from utils.themes import *

from screens.save_screen import SaveScreen
from screens.new_file_screen import NewFileScreen
from screens.new_folder_screen import NewFolderScreen
from screens.delete_screen import DeleteScreen

DEFAULT_THEME = moonstone
CONFIG_FILE = Path.cwd() / ".editor_config.json"


class StartupConfig:
    """Handle command line arguments and startup configuration."""
    
    def __init__(self):
        self.start_dir, self.initial_file = self._parse_arguments()
    
    def _parse_arguments(self) -> tuple[Path, Path | None]:
        """Parse command line arguments to determine start directory and initial file."""
        if len(sys.argv) > 1:
            if len(sys.argv) > 2:
                # Both directory and filename provided
                start_dir = Path(sys.argv[1])
                initial_file = Path(sys.argv[1]) / sys.argv[2]
                # If the filename argument is an absolute path, use it directly
                if Path(sys.argv[2]).is_absolute():
                    initial_file = Path(sys.argv[2])
                    start_dir = initial_file.parent
                return start_dir, initial_file
            else:
                # Only directory provided
                return Path(sys.argv[1]), None
        else:
            # No arguments, use current directory
            return Path.cwd(), None


class ConfigManager:
    """Handle application configuration persistence."""
    
    def __init__(self, app):
        self.app = app
        self.config_file = CONFIG_FILE
    
    def load_config(self) -> dict:
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            self.app.notify(f"Error loading config: {e}", severity="warning")
        return {}
    
    def save_config(self, config: dict) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except OSError as e:
            self.app.notify(f"Error saving config: {e}", severity="error")
    
    def get_saved_theme(self) -> str:
        """Get the saved theme from config, or return default."""
        config = self.load_config()
        saved_theme = config.get('theme', DEFAULT_THEME.name)
        return saved_theme if saved_theme else DEFAULT_THEME.name
    
    def save_current_theme(self, theme: str) -> None:
        """Save the current theme to config."""
        config = self.load_config()
        config['theme'] = theme
        self.save_config(config)


class TabData:
    """Class to store data for each tab."""
    def __init__(self, path: Path, content: str, editor: TextArea):
        self.path = path
        self.original_content = content
        self.editor = editor
        self.is_modified = False


class TabManager:
    """Handle tab operations and management."""
    
    def __init__(self, app):
        self.app = app
        self.tab_data = {}
        self.tab_counter = 0
    
    def get_next_tab_id(self) -> str:
        """Generate a unique tab ID."""
        self.tab_counter += 1
        return f"tab_{self.tab_counter}"
    
    def has_unsaved_changes(self, tab_id: str = None) -> bool:
        """Check if a specific tab or the current tab has unsaved changes."""
        if tab_id is None:
            tabs = self.app.query_one(TabbedContent)
            if tabs.active_pane is None:
                return False
            tab_id = tabs.active_pane.id
        
        if tab_id not in self.tab_data:
            return False
        
        tab_data = self.tab_data[tab_id]
        return tab_data.editor.text != tab_data.original_content
    
    def has_any_unsaved_changes(self) -> bool:
        """Check if any tab has unsaved changes."""
        return any(self.has_unsaved_changes(tab_id) for tab_id in self.tab_data)
    
    def update_tab_title(self, tab_id: str) -> None:
        """Update a tab's title to show unsaved changes indicator."""
        if tab_id not in self.tab_data:
            return
        
        tabs = self.app.query_one(TabbedContent)
        tab_data = self.tab_data[tab_id]
        filename = tab_data.path.name
        has_changes = self.has_unsaved_changes(tab_id)
        
        tab_pane = tabs.get_pane(tab_id)
        if tab_pane:
            tab_pane.label = f"{filename} *" if has_changes else filename
    
    def find_tab_by_path(self, file_path: Path) -> str | None:
        """Find if a file is already open in a tab."""
        for tab_id, tab_data in self.tab_data.items():
            if tab_data.path == file_path:
                return tab_id
        return None
    
    def create_tab_data(self, path: Path, content: str, editor: TextArea) -> str:
        """Create new tab data and return the tab ID."""
        tab_id = self.get_next_tab_id()
        self.tab_data[tab_id] = TabData(path, content, editor)
        return tab_id
    
    def remove_tab_data(self, tab_id: str) -> None:
        """Remove tab data."""
        if tab_id in self.tab_data:
            del self.tab_data[tab_id]
    
    def get_tabs_for_path(self, path: Path, include_subdirectories: bool = False) -> list[str]:
        """Get all tabs that match a path or are in subdirectories."""
        tabs_to_close = []
        for tab_id, tab_data in self.tab_data.items():
            if (tab_data.path == path or 
                (include_subdirectories and path in tab_data.path.parents)):
                tabs_to_close.append(tab_id)
        return tabs_to_close


class FileOperations:
    """Handle file operations and validation."""
    
    @staticmethod
    def check_file_size(path: Path) -> int | None:
        """Check file size and return size in bytes, or None if error."""
        try:
            return path.stat().st_size
        except OSError:
            return None
    
    @staticmethod
    def read_file_content(path: Path) -> str | None:
        """Read file content, return None if it's a binary file."""
        try:
            return path.read_text(encoding="utf‑8")
        except UnicodeDecodeError:
            return None
    
    @staticmethod
    def get_language_from_extension(path: Path) -> str | None:
        """Get syntax highlighting language from file extension."""
        file_extension = path.suffix.lower()
        return LANGUAGE_MAP.get(file_extension, None)


class TextEditor(App):
    CSS = """
    Screen { layout: horizontal; }
    DirectoryTree { width: 15%; border: tall #444; }
    TabbedContent { 
        width: 1fr;
        border: tall #555;
    }
    TextArea {
        height: 1fr;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.startup_config = StartupConfig()
        self.config_manager = ConfigManager(self)
        self.tab_manager = TabManager(self)
        self.pending_file_path = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, time_format="%I:%M %p")
        yield DirectoryTree(self.startup_config.start_dir)
        
        with TabbedContent():
            pass  # We'll add tabs dynamically
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the application after mounting."""
        register_custom_themes(self)
        self._load_saved_theme()
        self._load_initial_content()
    
    def _load_saved_theme(self) -> None:
        """Load and apply saved theme."""
        saved_theme = self.config_manager.get_saved_theme()
        self.theme = saved_theme
        
        if saved_theme != DEFAULT_THEME.name:
            self.call_after_refresh(lambda: self.notify(f"Loaded saved theme: {saved_theme}"))
    
    def _load_initial_content(self) -> None:
        """Load initial file or create welcome tab."""
        initial_file = self.startup_config.initial_file
        if initial_file and initial_file.exists() and initial_file.is_file():
            self.load_file(initial_file)
        else:
            self.create_welcome_tab()

    # Theme management methods
    def get_textarea_theme(self) -> str:
        """Get the appropriate TextArea theme for the current app theme."""
        return TEXTAREA_THEME_MAP.get(self.theme, "monokai")

    def update_all_textarea_themes(self) -> None:
        """Update the theme of all TextArea editors to match the current app theme."""
        new_theme = self.get_textarea_theme()
        
        # Update all tab editors
        for tab_data in self.tab_manager.tab_data.values():
            tab_data.editor.theme = new_theme
        
        # Update welcome tab if it exists
        self._update_welcome_tab_theme(new_theme)

    def _update_welcome_tab_theme(self, theme: str) -> None:
        """Update welcome tab theme if it exists."""
        tabs = self.query_one(TabbedContent)
        try:
            welcome_pane = tabs.get_pane("welcome")
            if welcome_pane:
                welcome_editor = welcome_pane.query_one(TextArea)
                welcome_editor.theme = theme
        except (ValueError, NoMatches):
            pass

    def watch_theme(self, old_theme: str, new_theme: str) -> None:
        """Called when the app theme changes. Update all TextArea themes."""
        self.call_after_refresh(self.update_all_textarea_themes)
        self.config_manager.save_current_theme(new_theme)

    # Tab and title management
    def create_welcome_tab(self) -> None:
        """Create a welcome tab for when no files are open."""
        tabs = self.query_one(TabbedContent)
        welcome_content = self._get_welcome_content()
        
        editor = TextArea.code_editor(
            text=welcome_content,
            language="markdown",
            theme=self.get_textarea_theme(),
            show_line_numbers=True,
            soft_wrap=False,
            read_only=True
        )
        
        tabs.add_pane(TabPane("Welcome", editor, id="welcome"))

    def _get_welcome_content(self) -> str:
        """Generate welcome tab content."""
        return (
            "# Welcome to the Squeeshalami Text Editor\n\n"
            "# Getting Started:\n\n"
            "Open a file from the directory tree to start editing.\n"
            "Use Ctrl+N to create a new file.\n"
            "Use Ctrl+F to create a new folder.\n"
            "Use Ctrl+W to close a tab.\n"
            "Use Ctrl+Q to quit the editor.\n"
        )

    def update_title(self) -> None:
        """Update the window title to show current file and unsaved status."""
        tabs = self.query_one(TabbedContent)
        if tabs.active_pane and tabs.active_pane.id in self.tab_manager.tab_data:
            tab_data = self.tab_manager.tab_data[tabs.active_pane.id]
            filename = tab_data.path.name
            has_changes = self.tab_manager.has_unsaved_changes(tabs.active_pane.id)
            if has_changes:
                self.title = f"Squeeshalami Text Editor - {filename} *"
            else:
                self.title = f"Squeeshalami Text Editor - {filename}"
        else:
            self.title = "Squeeshalami Text Editor"

    # File loading and management
    def load_file(self, path: Path) -> None:
        """Load a file into a new tab."""
        # Check if file is already open
        existing_tab_id = self.tab_manager.find_tab_by_path(path)
        if existing_tab_id:
            tabs = self.query_one(TabbedContent)
            tabs.active = existing_tab_id
            return
        
        # Validate file size
        file_size = FileOperations.check_file_size(path)
        if file_size and file_size > 10 * 1024 * 1024:  # 10MB
            self.notify(f"Large file detected ({file_size // 1024 // 1024}MB). Loading may be slow.", severity="warning")
        
        # Read file content
        text = FileOperations.read_file_content(path)
        if text is None:
            self.bell()  # binary file
            return
        
        # Create editor and tab
        editor = self._create_file_editor(path, text)
        tab_id = self.tab_manager.create_tab_data(path, text, editor)
        
        self._add_tab_to_ui(tab_id, path, editor)
        self._cleanup_welcome_tab()
        
        editor.focus()
        self.update_title()

    def _create_file_editor(self, path: Path, text: str) -> TextArea:
        """Create a TextArea editor for a file."""
        language = FileOperations.get_language_from_extension(path)
        return TextArea.code_editor(
            text=text,
            language=language,
            theme=self.get_textarea_theme(),
            show_line_numbers=True,
            soft_wrap=False,
        )

    def _add_tab_to_ui(self, tab_id: str, path: Path, editor: TextArea) -> None:
        """Add a tab to the UI."""
        tabs = self.query_one(TabbedContent)
        tab_pane = TabPane(path.name, editor, id=tab_id)
        tabs.add_pane(tab_pane)
        tabs.active = tab_id

    def _cleanup_welcome_tab(self) -> None:
        """Remove welcome tab if it exists."""
        tabs = self.query_one(TabbedContent)
        try:
            welcome_pane = tabs.get_pane("welcome")
            if welcome_pane:
                tabs.remove_pane("welcome")
        except (ValueError, NoMatches):
            pass

    # Event handlers
    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        file_path = Path(event.path)
        
        # Check if file is already open in a tab
        existing_tab_id = self.tab_manager.find_tab_by_path(file_path)
        if existing_tab_id:
            tabs = self.query_one(TabbedContent)
            tabs.active = existing_tab_id
            return
        
        self.load_file(file_path)
    
    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle text changes in any editor."""
        # Find which tab this editor belongs to
        for tab_id, tab_data in self.tab_manager.tab_data.items():
            if tab_data.editor is event.text_area:
                self.tab_manager.update_tab_title(tab_id)
                self.update_title()
                break

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """Handle tab switching."""
        self.update_title()
        if event.tab.id in self.tab_manager.tab_data:
            tab_data = self.tab_manager.tab_data[event.tab.id]
            tab_data.editor.focus()

    def on_resize(self, event: Resize) -> None:
        """Handle window resize events."""
        self.call_after_refresh(lambda: None)

    # Action methods and key bindings
    BINDINGS = [
        ("ctrl+s", "save", "Save"),
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+n", "new_file", "New File"),
        ("ctrl+f", "new_folder", "New Folder"),
        ("ctrl+w", "close_tab", "Close Tab"),
        ("delete", "delete_item", "Delete"),
    ]

    def action_save(self) -> None:
        """Save the current tab's file."""
        tabs = self.query_one(TabbedContent)
        if not tabs.active_pane or tabs.active_pane.id not in self.tab_manager.tab_data:
            return
        
        tab_id = tabs.active_pane.id
        tab_data = self.tab_manager.tab_data[tab_id]
        
        tab_data.path.write_text(tab_data.editor.text, encoding="utf‑8")
        tab_data.original_content = tab_data.editor.text
        self.tab_manager.update_tab_title(tab_id)
        self.update_title()
        self.notify(f"Saved {tab_data.path}")

    def action_close_tab(self) -> None:
        """Close the current tab."""
        tabs = self.query_one(TabbedContent)
        if not tabs.active_pane:
            return
        
        tab_id = tabs.active_pane.id
        
        if self.tab_manager.has_unsaved_changes(tab_id):
            self.close_tab_with_confirmation(tab_id)
        else:
            self._close_tab(tab_id)

    def action_new_file(self) -> None:
        self.create_new_file()
    
    def action_new_folder(self) -> None:
        self.create_new_folder()
    
    def action_delete_item(self) -> None:
        self.delete_selected_item()

    def action_quit(self) -> None:
        if self.tab_manager.has_any_unsaved_changes():
            self.quit_with_confirmation()
        else:
            self.exit()

    # File operation workflows
    @work(exclusive=True)
    async def switch_file_with_confirmation(self) -> None:
        """Show confirmation dialog when switching files with unsaved changes."""
        result = await self.push_screen_wait(SaveScreen())
        if result == "save": 
            self.action_save()
            self.load_file(self.pending_file_path)
        elif result == "discard": 
            self.load_file(self.pending_file_path)

    @work(exclusive=True)
    async def close_tab_with_confirmation(self, tab_id: str) -> None:
        """Show confirmation dialog when closing tab with unsaved changes."""
        result = await self.push_screen_wait(SaveScreen())
        if result == "save": 
            tabs = self.query_one(TabbedContent)
            if tabs.active_pane and tabs.active_pane.id == tab_id:
                self.action_save()
            self._close_tab(tab_id)
        elif result == "discard": 
            self._close_tab(tab_id)

    def _close_tab(self, tab_id: str) -> None:
        """Close a tab without confirmation."""
        tabs = self.query_one(TabbedContent)
        
        self.tab_manager.remove_tab_data(tab_id)
        tabs.remove_pane(tab_id)
        
        if not tabs.tab_count:
            self.create_welcome_tab()
        
        self.update_title()

    @work(exclusive=True)
    async def create_new_file(self) -> None:
        """Show new file dialog and handle the response."""
        result = await self.push_screen_wait(NewFileScreen())
        if result:
            target_dir = self._get_target_directory()
            new_file_path = target_dir / result
            
            if await self._create_file(new_file_path, result):
                directory_tree = self.query_one(DirectoryTree)
                directory_tree.reload()
                self.load_file(new_file_path)

    @work(exclusive=True)
    async def create_new_folder(self) -> None:
        """Show new folder dialog and handle the response."""
        result = await self.push_screen_wait(NewFolderScreen())
        if result:
            target_dir = self._get_target_directory()
            new_folder_path = target_dir / result
            
            if await self._create_folder(new_folder_path, result):
                directory_tree = self.query_one(DirectoryTree)
                directory_tree.reload()

    def _get_target_directory(self) -> Path:
        """Get the target directory for new files/folders based on selection."""
        directory_tree = self.query_one(DirectoryTree)
        
        if directory_tree.cursor_node is not None:
            selected_path = Path(directory_tree.cursor_node.data.path)
            return selected_path.parent if selected_path.is_file() else selected_path
        else:
            return self.startup_config.start_dir

    async def _create_file(self, file_path: Path, filename: str) -> bool:
        """Create a new file, return True if successful."""
        try:
            if file_path.exists():
                self.notify(f"File {filename} already exists!", severity="warning")
                return False
            
            file_path.write_text("", encoding="utf-8")
            self.notify(f"Created {file_path}")
            return True
            
        except Exception as e:
            self.notify(f"Error creating file: {str(e)}", severity="error")
            return False

    async def _create_folder(self, folder_path: Path, foldername: str) -> bool:
        """Create a new folder, return True if successful."""
        try:
            if folder_path.exists():
                self.notify(f"Folder {foldername} already exists!", severity="warning")
                return False
            
            folder_path.mkdir(parents=True, exist_ok=False)
            self.notify(f"Created folder {folder_path}")
            return True
            
        except Exception as e:
            self.notify(f"Error creating folder: {str(e)}", severity="error")
            return False

    @work(exclusive=True)
    async def delete_selected_item(self) -> None:
        """Show delete confirmation dialog and handle the response."""
        directory_tree = self.query_one(DirectoryTree)
        
        if directory_tree.cursor_node is None:
            self.notify("No item selected for deletion", severity="warning")
            return
        
        selected_path = Path(directory_tree.cursor_node.data.path)
        
        if selected_path == self.startup_config.start_dir:
            self.notify("Cannot delete the root directory", severity="error")
            return
        
        is_directory = selected_path.is_dir()
        item_name = selected_path.name
        
        result = await self.push_screen_wait(DeleteScreen(item_name, is_directory))
        
        if result == "delete":
            if await self._delete_item(selected_path, is_directory, item_name):
                directory_tree.reload()

    async def _delete_item(self, path: Path, is_directory: bool, item_name: str) -> bool:
        """Delete an item and close related tabs, return True if successful."""
        try:
            # Close affected tabs
            tabs_to_close = self.tab_manager.get_tabs_for_path(path, include_subdirectories=is_directory)
            for tab_id in tabs_to_close:
                self._close_tab(tab_id)
            
            # Delete the item
            if is_directory:
                shutil.rmtree(path)
                self.notify(f"Deleted folder: {item_name}")
            else:
                path.unlink()
                self.notify(f"Deleted file: {item_name}")
            
            return True
            
        except Exception as e:
            self.notify(f"Error deleting {item_name}: {str(e)}", severity="error")
            return False

    @work(exclusive=True)
    async def quit_with_confirmation(self) -> None:
        """Show confirmation dialog before quitting with unsaved changes."""
        result = await self.push_screen_wait(SaveScreen())
        if result == "save":
            self._save_all_modified_tabs()
            self.exit()
        elif result == "discard":
            self.exit()

    def _save_all_modified_tabs(self) -> None:
        """Save all tabs with unsaved changes."""
        tabs = self.query_one(TabbedContent)
        for tab_id in self.tab_manager.tab_data:
            if self.tab_manager.has_unsaved_changes(tab_id):
                tabs.active = tab_id
                self.action_save()


if __name__ == "__main__":
    TextEditor().run()
