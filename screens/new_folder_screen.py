from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Label, Input


class NewFolderScreen(ModalScreen[str]):
    """Screen with a dialog to create a new folder."""
    
    BINDINGS = [("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    NewFolderScreen {
        align: center middle;
    }

    #dialog {
        padding: 1 2;
        width: 50;
        height: 9;
        border: thick $background 80%;
        background: $surface;
    }

    #foldername-input {
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

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Enter the folder name:")
            yield Input(placeholder="new_folder", id="foldername-input")
            with Horizontal(id="buttons"):
                yield Button("Create", variant="primary", id="create")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        self.call_after_refresh(self._focus_input)
    
    def _focus_input(self) -> None:
        input_widget = self.query_one("#foldername-input", Input)
        input_widget.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create":
            foldername = self.query_one("#foldername-input", Input).value.strip()
            if foldername:  # Only create if foldername is not empty
                self.dismiss(foldername)
            else:
                # Stay in dialog if no foldername entered
                self.query_one("#foldername-input", Input).focus()
        else:
            self.dismiss(None)  # Cancel - return None

    def on_input_submitted(self, event: Input.Submitted) -> None:
        foldername = event.value.strip()
        if foldername:
            self.dismiss(foldername)
    
    def action_cancel(self) -> None:
        self.dismiss(None)
