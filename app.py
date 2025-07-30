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

from utils.utils import LANGUAGE_MAP, TEXTAREA_THEME_MAP, AVAILABLE_THEMES, register_custom_themes
from utils.themes import *

from screens.save_screen import SaveScreen
from screens.new_file_screen import NewFileScreen
from screens.new_folder_screen import NewFolderScreen
from screens.delete_screen import DeleteScreen

DEFAULT_THEME = moonstone

# Configuration file path
CONFIG_FILE = Path.cwd() / ".editor_config.json"

# Handle command line arguments: directory and optional filename
if len(sys.argv) > 1:
    if len(sys.argv) > 2:
        # Both directory and filename provided
        START_DIR = Path(sys.argv[1])
        INITIAL_FILE = Path(sys.argv[1]) / sys.argv[2]
        # If the filename argument is an absolute path, use it directly
        if Path(sys.argv[2]).is_absolute():
            INITIAL_FILE = Path(sys.argv[2])
            START_DIR = INITIAL_FILE.parent
    else:
        # Only directory provided
        START_DIR = Path(sys.argv[1])
        INITIAL_FILE = None
else:
    # No arguments, use current directory
    START_DIR = Path.cwd()
    INITIAL_FILE = None


class TabData:
    """Class to store data for each tab."""
    def __init__(self, path: Path, content: str, editor: TextArea):
        self.path = path
        self.original_content = content
        self.editor = editor  # Direct reference to the TextArea
        self.is_modified = False

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
        self.tab_data = {}  # Store TabData objects keyed by tab id
        self.tab_counter = 0  # Counter for unique tab IDs
        self.pending_file_path = None  # Store file path when switching with unsaved changes
        self.current_theme_index = 0  # For theme cycling

    def load_config(self) -> dict:
        """Load configuration from file."""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            self.notify(f"Error loading config: {e}", severity="warning")
        return {}

    def save_config(self, config: dict) -> None:
        """Save configuration to file."""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        except OSError as e:
            self.notify(f"Error saving config: {e}", severity="error")

    def get_saved_theme(self) -> str:
        """Get the saved theme from config, or return default."""
        config = self.load_config()
        saved_theme = config.get('theme', DEFAULT_THEME.name)
        
        # Ensure the saved theme is valid
        if saved_theme in AVAILABLE_THEMES:
            return saved_theme
        else:
            return DEFAULT_THEME.name

    def save_current_theme(self) -> None:
        """Save the current theme to config."""
        config = self.load_config()
        config['theme'] = self.theme
        self.save_config(config)

    def get_textarea_theme(self) -> str:
        """Get the appropriate TextArea theme for the current app theme."""
        return TEXTAREA_THEME_MAP.get(self.theme, "monokai")

    def update_all_textarea_themes(self) -> None:
        """Update the theme of all TextArea editors to match the current app theme."""
        new_theme = self.get_textarea_theme()
        
        # Update all tab editors
        for tab_data in self.tab_data.values():
            tab_data.editor.theme = new_theme
        
        # Update welcome tab if it exists
        tabs = self.query_one(TabbedContent)
        try:
            welcome_pane = tabs.get_pane("welcome")
            if welcome_pane:
                welcome_editor = welcome_pane.query_one(TextArea)
                welcome_editor.theme = new_theme
        except (ValueError, NoMatches):
            pass

    def watch_theme(self, old_theme: str, new_theme: str) -> None:
        """Called when the app theme changes. Update all TextArea themes."""
        self.call_after_refresh(self.update_all_textarea_themes)
        # Save the new theme to config
        self.save_current_theme()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, time_format="%I:%M %p")
        
        yield DirectoryTree(START_DIR)
        
        # Create TabbedContent with an initial empty tab
        with TabbedContent():
            pass  # We'll add tabs dynamically
        
        yield Footer()
    
    def on_mount(self) -> None:
        register_custom_themes(self)
        
        # Load the saved theme or use default
        saved_theme = self.get_saved_theme()
        self.theme = saved_theme
        
        # Notify user if we loaded a saved theme (but not the default)
        if saved_theme != DEFAULT_THEME.name:
            self.call_after_refresh(lambda: self.notify(f"Loaded saved theme: {saved_theme}"))
        
        # Initialize theme index for cycling
        if self.theme in AVAILABLE_THEMES:
            self.current_theme_index = AVAILABLE_THEMES.index(self.theme)
        
        if INITIAL_FILE and INITIAL_FILE.exists() and INITIAL_FILE.is_file():
            self.load_file(INITIAL_FILE)
        else:
            # Create a welcome tab if no initial file
            self._create_welcome_tab()

    def _create_welcome_tab(self) -> None:
        """Create a welcome tab for when no files are open."""
        tabs = self.query_one(TabbedContent)
        welcome_content = "# Welcome to the Squeeshalami Text Editor\n\n"
        welcome_content += "Open a file from the directory tree to start editing.\n"
        welcome_content += "Use Ctrl+N to create a new file.\n"
        welcome_content += "Use Ctrl+T to cycle through themes.\n"
        welcome_content += "Your theme preference will be remembered between sessions.\n"
        
        editor = TextArea.code_editor(
            text=welcome_content,
            language="markdown",
            theme=self.get_textarea_theme(),
            show_line_numbers=True,
            soft_wrap=False,
            read_only=True
        )
        
        tabs.add_pane(TabPane("Welcome", editor, id="welcome"))

    def _get_next_tab_id(self) -> str:
        """Generate a unique tab ID."""
        self.tab_counter += 1
        return f"tab_{self.tab_counter}"

    def has_unsaved_changes(self, tab_id: str = None) -> bool:
        """Check if a specific tab or the current tab has unsaved changes."""
        if tab_id is None:
            tabs = self.query_one(TabbedContent)
            if tabs.active_pane is None:
                return False
            tab_id = tabs.active_pane.id
        
        if tab_id not in self.tab_data:
            return False
        
        tab_data = self.tab_data[tab_id]
        return tab_data.editor.text != tab_data.original_content

    def has_any_unsaved_changes(self) -> bool:
        """Check if any tab has unsaved changes."""
        for tab_id in self.tab_data:
            if self.has_unsaved_changes(tab_id):
                return True
        return False

    def update_title(self) -> None:
        """Update the window title to show current file and unsaved status."""
        tabs = self.query_one(TabbedContent)
        if tabs.active_pane and tabs.active_pane.id in self.tab_data:
            tab_data = self.tab_data[tabs.active_pane.id]
            filename = tab_data.path.name
            has_changes = self.has_unsaved_changes(tabs.active_pane.id)
            if has_changes:
                self.title = f"Squeeshalami Text Editor - {filename} *"
            else:
                self.title = f"Squeeshalami Text Editor - {filename}"
        else:
            self.title = "Squeeshalami Text Editor"

    def update_tab_title(self, tab_id: str) -> None:
        if tab_id not in self.tab_data:
            return
        
        tabs = self.query_one(TabbedContent)
        tab_data = self.tab_data[tab_id]
        filename = tab_data.path.name
        has_changes = self.has_unsaved_changes(tab_id)
        
        # Update the tab label
        tab_pane = tabs.get_pane(tab_id)
        if tab_pane:
            if has_changes:
                tab_pane.label = f"{filename} *"
            else:
                tab_pane.label = filename

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        file_path = Path(event.path)
        
        # Check if file is already open in a tab
        for tab_id, tab_data in self.tab_data.items():
            if tab_data.path == file_path:
                # Switch to existing tab
                tabs = self.query_one(TabbedContent)
                tabs.active = tab_id
                return
        
        # Load file in new tab
        self.load_file(file_path)
    
    @work(exclusive=True)
    async def switch_file_with_confirmation(self) -> None:
        """Show confirmation dialog when switching files with unsaved changes."""
        result = await self.push_screen_wait(SaveScreen())
        if result == "save": 
            self.action_save()
            self.load_file(self.pending_file_path)
        elif result == "discard": 
            self.load_file(self.pending_file_path)
        
    def load_file(self, path: Path) -> None:
        """Load a file into a new tab."""
        # Check file size and warn for large files
        try:
            file_size = path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB
                self.notify(f"Large file detected ({file_size // 1024 // 1024}MB). Loading may be slow.", severity="warning")
        except OSError:
            pass
        
        try:
            text = path.read_text(encoding="utf‑8")
        except UnicodeDecodeError:
            self.bell()   # binary file
            return
        
        # Set syntax highlighting based on file extension
        file_extension = path.suffix.lower()
        language = LANGUAGE_MAP.get(file_extension, None)
        
        # Create new editor for this file
        editor = TextArea.code_editor(
            text=text,
            language=language,
            theme=self.get_textarea_theme(),
            show_line_numbers=True,
            soft_wrap=False,
        )
        
        # Generate unique tab ID and create tab data
        tab_id = self._get_next_tab_id()
        self.tab_data[tab_id] = TabData(path, text, editor)
        
        # Add tab to TabbedContent
        tabs = self.query_one(TabbedContent)
        
        # Remove welcome tab if it exists
        try:
            welcome_pane = tabs.get_pane("welcome")
            if welcome_pane:
                tabs.remove_pane("welcome")
        except (ValueError, NoMatches):
            # Welcome tab doesn't exist, which is fine
            pass
        
        tab_pane = TabPane(path.name, editor, id=tab_id)
        tabs.add_pane(tab_pane)
        tabs.active = tab_id
        
        editor.focus()
        self.update_title()
    
    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle text changes in any editor."""
        # Find which tab this editor belongs to by comparing the editor reference
        for tab_id, tab_data in self.tab_data.items():
            if tab_data.editor is event.text_area:
                self.update_tab_title(tab_id)
                self.update_title()
                break

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """Handle tab switching."""
        self.update_title()
        # Focus the editor in the active tab
        if event.tab.id in self.tab_data:
            tab_data = self.tab_data[event.tab.id]
            tab_data.editor.focus()

    def on_resize(self, event: Resize) -> None:
        # Force a refresh of the layout to prevent visual artifacts
        self.call_after_refresh(lambda: None)

    ### Key bindings ###
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
        if not tabs.active_pane or tabs.active_pane.id not in self.tab_data:
            return
        
        tab_id = tabs.active_pane.id
        tab_data = self.tab_data[tab_id]
        
        tab_data.path.write_text(tab_data.editor.text, encoding="utf‑8")
        tab_data.original_content = tab_data.editor.text  # Update original content after save
        self.update_tab_title(tab_id)  # Update tab title to remove unsaved indicator
        self.update_title()  # Update window title
        self.notify(f"Saved {tab_data.path}")

    def action_close_tab(self) -> None:
        """Close the current tab."""
        tabs = self.query_one(TabbedContent)
        if not tabs.active_pane:
            return
        
        tab_id = tabs.active_pane.id
        
        # Check for unsaved changes
        if self.has_unsaved_changes(tab_id):
            self.close_tab_with_confirmation(tab_id)
        else:
            self._close_tab(tab_id)

    @work(exclusive=True)
    async def close_tab_with_confirmation(self, tab_id: str) -> None:
        """Show confirmation dialog when closing tab with unsaved changes."""
        result = await self.push_screen_wait(SaveScreen())
        if result == "save": 
            # Save current tab first
            tabs = self.query_one(TabbedContent)
            if tabs.active_pane and tabs.active_pane.id == tab_id:
                self.action_save()
            self._close_tab(tab_id)
        elif result == "discard": 
            self._close_tab(tab_id)

    def _close_tab(self, tab_id: str) -> None:
        """Close a tab without confirmation."""
        tabs = self.query_one(TabbedContent)
        
        # Remove tab data
        if tab_id in self.tab_data:
            del self.tab_data[tab_id]
        
        # Remove the tab pane
        tabs.remove_pane(tab_id)
        
        # If no tabs left, show welcome tab
        if not tabs.tab_count:
            self._create_welcome_tab()
        
        self.update_title()
    
    def action_new_file(self) -> None:
        self.create_new_file()
    
    def action_new_folder(self) -> None:
        self.create_new_folder()
    
    def action_delete_item(self) -> None:
        self.delete_selected_item()
    
    @work(exclusive=True)
    async def create_new_file(self) -> None:
        """Show new file dialog and handle the response."""
        result = await self.push_screen_wait(NewFileScreen())
        if result:  # If user provided a filename (not cancelled)
            # Get the currently selected directory from the directory tree
            directory_tree = self.query_one(DirectoryTree)
            
            # Get the selected directory path
            if directory_tree.cursor_node is not None:
                # Get the data from the selected node
                selected_path = Path(directory_tree.cursor_node.data.path)
                # If selected item is a file, get its parent directory
                if selected_path.is_file():
                    target_dir = selected_path.parent
                else:
                    target_dir = selected_path
            else:
                # If no selection, use the root directory
                target_dir = START_DIR
            
            # Create the full path for the new file
            new_file_path = target_dir / result
            
            try:
                # Create the file (only if it doesn't exist)
                if new_file_path.exists():
                    self.notify(f"File {result} already exists!", severity="warning")
                    return
                
                # Create the file with empty content
                new_file_path.write_text("", encoding="utf-8")
                self.notify(f"Created {new_file_path}")
                
                # Refresh the directory tree to show the new file
                directory_tree.reload()
                
                # Load the new file in the editor
                self.load_file(new_file_path)
                
            except Exception as e:
                self.notify(f"Error creating file: {str(e)}", severity="error")
    
    @work(exclusive=True)
    async def create_new_folder(self) -> None:
        """Show new folder dialog and handle the response."""
        result = await self.push_screen_wait(NewFolderScreen())
        if result:  # If user provided a folder name (not cancelled)
            # Get the currently selected directory from the directory tree
            directory_tree = self.query_one(DirectoryTree)
            
            # Get the selected directory path
            if directory_tree.cursor_node is not None:
                # Get the data from the selected node
                selected_path = Path(directory_tree.cursor_node.data.path)
                # If selected item is a file, get its parent directory
                if selected_path.is_file():
                    target_dir = selected_path.parent
                else:
                    target_dir = selected_path
            else:
                # If no selection, use the root directory
                target_dir = START_DIR
            
            # Create the full path for the new folder
            new_folder_path = target_dir / result
            
            try:
                # Create the folder (only if it doesn't exist)
                if new_folder_path.exists():
                    self.notify(f"Folder {result} already exists!", severity="warning")
                    return
                
                # Create the folder
                new_folder_path.mkdir(parents=True, exist_ok=False)
                self.notify(f"Created folder {new_folder_path}")
                
                # Refresh the directory tree to show the new folder
                directory_tree.reload()
                
            except Exception as e:
                self.notify(f"Error creating folder: {str(e)}", severity="error")
    
    @work(exclusive=True)
    async def delete_selected_item(self) -> None:
        """Show delete confirmation dialog and handle the response."""
        # Get the currently selected item from the directory tree  
        directory_tree = self.query_one(DirectoryTree)
        
        if directory_tree.cursor_node is None:
            self.notify("No item selected for deletion", severity="warning")
            return
        
        # Get the selected path
        selected_path = Path(directory_tree.cursor_node.data.path)
        
        # Don't allow deleting the root directory
        if selected_path == START_DIR:
            self.notify("Cannot delete the root directory", severity="error")
            return
        
        # Determine if it's a directory or file
        is_directory = selected_path.is_dir()
        item_name = selected_path.name
        
        # Show confirmation dialog
        result = await self.push_screen_wait(DeleteScreen(item_name, is_directory))
        
        if result == "delete":
            try:
                # Close any tabs that have this file or files in this directory
                tabs_to_close = []
                for tab_id, tab_data in self.tab_data.items():
                    if (tab_data.path == selected_path or 
                        (is_directory and selected_path in tab_data.path.parents)):
                        tabs_to_close.append(tab_id)
                
                # Close the affected tabs
                for tab_id in tabs_to_close:
                    self._close_tab(tab_id)
                
                # Delete the item
                if is_directory:
                    # Delete directory and all its contents
                    shutil.rmtree(selected_path)
                    self.notify(f"Deleted folder: {item_name}")
                else:
                    # Delete file
                    selected_path.unlink()
                    self.notify(f"Deleted file: {item_name}")
                
                # Refresh the directory tree to show the changes
                directory_tree.reload()
                
            except Exception as e:
                self.notify(f"Error deleting {item_name}: {str(e)}", severity="error")
    
    def action_quit(self) -> None:
        if self.has_any_unsaved_changes():
            self.quit_with_confirmation()
        else:
            self.exit()
    
    @work(exclusive=True)
    async def quit_with_confirmation(self) -> None:
        # TODO: In a more advanced implementation, you might want to show
        # which specific tabs have unsaved changes
        result = await self.push_screen_wait(SaveScreen())
        if result == "save":
            # Save all modified tabs
            for tab_id in self.tab_data:
                if self.has_unsaved_changes(tab_id):
                    tabs = self.query_one(TabbedContent)
                    tabs.active = tab_id  # Switch to tab to save it
                    self.action_save()
            self.exit()
        elif result == "discard":
            self.exit()

if __name__ == "__main__":
    TextEditor().run()
