from reactpy import component, html, run

# Define a function that return a button, which on clicking executes
# Python function "handle_event" (prints some text)
@component
def PrintButton(display_text, message_text):
    def handle_event(event):
        print(message_text)

    return html.button({"on_click": handle_event}, display_text)

@component
def App():
    return html.div(
        PrintButton("record", "Playing"),
        PrintButton("stop", "Paused"),
    )

run(App)