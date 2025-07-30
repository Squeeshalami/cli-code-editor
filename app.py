from __future__ import annotations
from pathlib import Path
import sys
import shutil

from textual.app import App, ComposeResult
from textual.widgets import DirectoryTree, TextArea, Footer, Header
from textual.events import Key, Resize
from textual import work

from utils.utils import LANGUAGE_MAP, register_custom_themes
from utils.themes import *

from screens.save_screen import SaveScreen
from screens.new_file_screen import NewFileScreen
from screens.new_folder_screen import NewFolderScreen
from screens.delete_screen import DeleteScreen

DEFAULT_THEME = ember

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


class TextEditor(App):
    CSS = """
    Screen { layout: horizontal; }
    DirectoryTree { width: 15%; border: tall #444; }
    TextArea { 
        width: 1fr;
        border: tall #555;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.original_content = ""  # Track original file content
        self.current_path = None    # Track current file path
        self.pending_file_path = None  # Store file path when switching with unsaved changes

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, time_format="%I:%M %p")
        
        yield DirectoryTree(START_DIR)
        self.editor = TextArea.code_editor(
            language="python",
            theme="monokai",
            show_line_numbers=True,
            soft_wrap=False,
            
        )
        yield self.editor
        yield Footer()
    
    def on_mount(self) -> None:
        register_custom_themes(self)
        self.theme = DEFAULT_THEME.name
        
        if INITIAL_FILE and INITIAL_FILE.exists() and INITIAL_FILE.is_file():
            self.load_file(INITIAL_FILE)

    def has_unsaved_changes(self) -> bool:
        if not hasattr(self, 'current_path') or self.current_path is None:
            return False
        return self.editor.text != self.original_content
    
    def update_title(self) -> None:
        """Update the window title to show current file and unsaved status."""
        if self.current_path:
            filename = self.current_path.name
            if self.has_unsaved_changes():
                self.title = f"Squeeshalami Text Editor - {filename} *"
            else:
                self.title = f"Squeeshalami Text Editor - {filename}"
        else:
            self.title = "Squeeshalami Text Editor"

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        # Check for unsaved changes before switching files
        if self.has_unsaved_changes():
            self.pending_file_path = Path(event.path)  # Store the file to switch to
            self.switch_file_with_confirmation()
        else:
            self.load_file(Path(event.path))
    
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
        """Load a file into the editor."""
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
        try:
            self.editor.language = language
        except Exception:
            # If language is not supported, fall back to plain text
            self.editor.language = None
        
        self.editor.text = text
        self.original_content = text
        self.editor.focus()
        self.current_path = path      # remember where to save
        self.update_title()
    
    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        self.update_title()

    def on_resize(self, event: Resize) -> None:
        # Force a refresh of the layout to prevent visual artifacts
        self.call_after_refresh(lambda: None)

    ### Key bindings ###
    BINDINGS = [
        ("ctrl+s", "save", "Save"),
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+n", "new_file", "New File"),
        ("ctrl+f", "new_folder", "New Folder"),
        ("delete", "delete_item", "Delete"),
        ]

    def action_save(self) -> None:
        if not hasattr(self, "current_path") or self.current_path is None:
            return
        self.current_path.write_text(self.editor.text, encoding="utf‑8")
        self.original_content = self.editor.text  # Update original content after save
        self.update_title()  # Update title to remove unsaved indicator
        self.notify(f"Saved {self.current_path}")
    
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
                # Check if we're deleting the currently opened file
                if hasattr(self, 'current_path') and self.current_path == selected_path:
                    # Clear the editor if we're deleting the current file
                    self.editor.text = ""
                    self.original_content = ""
                    self.current_path = None
                    self.update_title()
                
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
        if self.has_unsaved_changes():
            self.quit_with_confirmation()
        else:
            self.exit()
    
    @work(exclusive=True)
    async def quit_with_confirmation(self) -> None:
        result = await self.push_screen_wait(SaveScreen())
        if result == "save":
            self.action_save()
            self.exit()
        elif result == "discard":
            self.exit()

if __name__ == "__main__":
    TextEditor().run()
