from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Label, Input


class NewFileScreen(ModalScreen[str]):
    """Screen with a dialog to create a new file."""
    
    BINDINGS = [("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    NewFileScreen {
        align: center middle;
    }

    #dialog {
        padding: 1 2;
        width: 50;
        height: 9;
        border: thick $background 80%;
        background: $surface;
    }

    #filename-input {
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
            yield Label("Enter the filename:")
            yield Input(placeholder="filename.py", id="filename-input")
            with Horizontal(id="buttons"):
                yield Button("Create", variant="primary", id="create")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        self.call_after_refresh(self._focus_input)
    
    def _focus_input(self) -> None:
        """Helper method to focus the input field."""
        input_widget = self.query_one("#filename-input", Input)
        input_widget.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create":
            filename = self.query_one("#filename-input", Input).value.strip()
            if filename:  # Only create if filename is not empty
                self.dismiss(filename)
            else:
                # Stay in dialog if no filename entered
                self.query_one("#filename-input", Input).focus()
        else:
            self.dismiss(None)  # Cancel - return None

    def on_input_submitted(self, event: Input.Submitted) -> None:
        filename = event.value.strip()
        if filename:
            self.dismiss(filename)
    
    def action_cancel(self) -> None:
        self.dismiss(None)
