from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Grid
from textual.widgets import Button, Label


class SaveScreen(ModalScreen[str]):
    """Screen with a dialog to save or discard unsaved changes."""

    BINDINGS = [("escape", "cancel", "Cancel")]


    DEFAULT_CSS = """
    SaveScreen {
        align: center middle;
    }

    #dialog {
        grid-size: 3;
        grid-gutter: 0 1;
        grid-rows: 2 5;
        padding: 1;
        width: 80;
        height: 12;
        border: solid $primary;
        background: $surface;
    }

    #question {
        column-span: 3;
        height: 2fr;
        width: 1fr;
        content-align: center middle;
        text-style: bold;
    }

    SaveScreen Button {
        width: 90%;
        height: 5;
        margin: 0;
        padding: 1;
        box-sizing: border-box;
        content-align: center middle;
        color: #FFFFFF;
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("You have unsaved changes. What would you like to do?", id="question"),
            Button("Save", variant="primary", id="save"),
            Button("Discard", variant="error", id="discard"),
            Button("Cancel", variant="default", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.dismiss("save")
        elif event.button.id == "discard":
            self.dismiss("discard")
        else:
            self.dismiss("cancel")

    def action_cancel(self) -> None:
        self.dismiss(None)