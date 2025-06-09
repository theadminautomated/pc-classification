# This module contains the main application window and entrypoint for the Records Classifier GUI.
# It delegates screens, widgets, and business logic to their respective modules for maintainability.

import tkinter as tk
import customtkinter as ctk
import asyncio # Import asyncio
from .screens import SetupScreen, MainScreen  # Import MainScreen
from .theme import theme

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class RecordsClassifierApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Pierce County Records Classifier")
        self.geometry("1024x768")
        self.configure(fg_color=theme['bg'])  # Set background theme
        self._setup_main_ui()

        # Asyncio event loop integration
        self.async_loop = asyncio.get_event_loop()
        self.after(100, self._update_asyncio) # Start the asyncio update loop

    def _update_asyncio(self):
        """Run one iteration of the asyncio event loop and schedule the next."""
        self.async_loop.call_soon(self.async_loop.stop) # Stop the loop after current tasks
        self.async_loop.run_forever() # Run until stop()
        self.after(15, self._update_asyncio) # Schedule next update (e.g., ~60 FPS)

    def _setup_main_ui(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True)
        self.show_screen(SetupScreen, on_complete_callback=self._on_setup_complete)

    def _on_setup_complete(self, success=True):
        # Handle setup completion with success status
        if success:
            print("Setup complete, transitioning to main application...")
            self.show_screen(MainScreen) # Show MainScreen
        else:
            print("Setup failed! Please check the logs and try again.")
            # Could add error handling here or show an error screen

    def show_screen(self, screen_class, on_complete_callback=None):
        # Remove any existing screen 
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        screen_params = {'parent': self.main_frame}
        if screen_class == SetupScreen:
            if on_complete_callback:
                screen_params['on_complete'] = on_complete_callback
            # Use proper setup steps
            screen_params['steps'] = [
                {"name": "Checking Ollama service", "weight": 30},
                {"name": "Verifying model", "weight": 40},
                {"name": "Finalizing setup", "weight": 30}
            ]
            screen_params['task_name'] = "Initializing Services"
            screen_params['auto_run'] = True

        # Add the new screen
        screen = screen_class(**screen_params)
        screen.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = RecordsClassifierApp()
    app.mainloop()
