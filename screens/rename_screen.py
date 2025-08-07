from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Label, Input
from textual.binding import Binding


class RenameScreen(ModalScreen[str]):
    """Screen with a dialog to rename files and folders."""
    
    BINDINGS = [Binding("escape", "cancel", "Cancel", priority=True)]

    DEFAULT_CSS = """
    RenameScreen {
        align: center middle;
    }

    #dialog {
        padding: 1 2;
        width: 50;
        height: 9;
        border: thick $background 80%;
        background: $surface;
    }

    #name-input {
        margin: 1 0;
    }

    #buttons {
        align: center middle;
        height: 3;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(self, current_name: str, is_directory: bool, **kwargs):
        super().__init__(**kwargs)
        self.current_name = current_name
        self.is_directory = is_directory

    def compose(self) -> ComposeResult:
        item_type = "folder" if self.is_directory else "file"
        with Vertical(id="dialog"):
            yield Label(f"Rename {item_type}:")
            yield Input(value=self.current_name, id="name-input")
            with Horizontal(id="buttons"):
                yield Button("Rename", variant="primary", id="rename")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        self.call_after_refresh(self._focus_input)
    
    def _focus_input(self) -> None:
        """Helper method to focus the input field and select all text."""
        input_widget = self.query_one("#name-input", Input)
        input_widget.focus()
        # Select all text for easy replacement
        input_widget.text_select_all()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "rename":
            new_name = self.query_one("#name-input", Input).value.strip()
            if new_name and new_name != self.current_name:
                self.dismiss(new_name)
            elif not new_name:
                # Stay in dialog if no name entered
                self.query_one("#name-input", Input).focus()
            else:
                # Name unchanged, cancel
                self.dismiss(None)
        else:
            self.dismiss(None)  # Cancel - return None

    def on_input_submitted(self, event: Input.Submitted) -> None:
        new_name = event.value.strip()
        if new_name and new_name != self.current_name:
            self.dismiss(new_name)
        elif not new_name:
            # Stay in dialog if no name entered
            self.query_one("#name-input", Input).focus()
        else:
            # Name unchanged, cancel
            self.dismiss(None)
    
    def action_cancel(self) -> None:
        self.dismiss(None)
    
