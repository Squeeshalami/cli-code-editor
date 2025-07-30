from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Label


class DeleteScreen(ModalScreen[str]):
    """Screen with a dialog to confirm deletion of files/folders."""
    
    BINDINGS = [("escape", "cancel", "Cancel"), ("enter", "delete", "Delete")]

    DEFAULT_CSS = """
    DeleteScreen {
        align: center middle;
    }

    #dialog {
        padding: 1 2;
        width: 60;
        height: 18;
        border: thick $background 80%;
        background: $surface;
    }

    .warning {
        text-style: bold;
        color: $warning;
        text-align: center;
        margin: 1 0;
    }

    .message {
        text-align: center;
        margin: 1 0;
    }

    .hint {
        text-align: center;
        text-style: italic;
        color: $text-muted;
        margin: 1 0 0 0;
    }

    #buttons {
        align: center middle;
        height: 3;
        margin: 1 0;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(self, item_name: str, is_directory: bool, **kwargs):
        super().__init__(**kwargs)
        self.item_name = item_name
        self.is_directory = is_directory

    def compose(self) -> ComposeResult:
        item_type = "folder" if self.is_directory else "file"
        with Vertical(id="dialog"):
            yield Label("⚠️  WARNING", classes="warning")
            yield Label(f"Are you sure you want to delete the {item_type}:", classes="message")
            yield Label(f'"{self.item_name}"?', classes="message")
            with Horizontal(id="buttons"):
                yield Button("Delete", variant="error", id="delete")
                yield Button("Cancel", variant="default", id="cancel")
            yield Label("Press Enter to Delete, Esc to Cancel", classes="hint")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "delete":
            self.dismiss("delete")
        else:
            self.dismiss("cancel")
    
    def action_cancel(self) -> None:
        self.dismiss("cancel")
    
    def action_delete(self) -> None:
        self.dismiss("delete")
