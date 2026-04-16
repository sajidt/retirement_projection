"""GUI setup and management for the portfolio application."""

import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from datetime import datetime

# Reference to callbacks (will be set by main)
callbacks = {}


def set_callbacks(callback_dict):
    """Set the callback functions dictionary."""
    global callbacks
    callbacks = callback_dict


def create_gui(root):
    """
    Set up the main GUI window with menu bar and output box.
    
    Args:
        root: Tkinter root window
        
    Returns:
        ScrolledText widget for output
    """
    root.title("Investment Portfolio Summary")
    root.geometry("800x600")

    # Create menu bar
    menubar = tk.Menu(root)
    root.config(menu=menubar)

    # File menu
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Save Output", command=lambda: callbacks.get('save_output', lambda: None)())

    # Charts menu
    charts_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Charts", menu=charts_menu)
    charts_menu.add_command(label="View Investment History", command=lambda: callbacks.get('load_history', lambda: None)())
    charts_menu.add_command(label="Asset Allocation Chart", command=lambda: callbacks.get('draw_allocation', lambda: None)())
    charts_menu.add_command(label="View Future Value Chart", command=lambda: callbacks.get('show_future_value', lambda: None)())
    charts_menu.add_command(label="Annual Expense Capacity", command=lambda: callbacks.get('show_expense_predictor', lambda: None)())
    charts_menu.add_command(label="View Individual Performance", command=lambda: callbacks.get('show_individual_perf', lambda: None)())
    charts_menu.add_command(label="SWR Trends", command=lambda: callbacks.get('show_swr_trends', lambda: None)())

    output_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Courier New", 10))
    output_box.pack(expand=True, fill="both")

    return output_box


def gui_print(output_box, msg):
    """
    Print message to the output box.
    
    Args:
        output_box: ScrolledText widget
        msg: Message to print
    """
    output_box.insert(tk.END, msg + "\n")
    output_box.see(tk.END)


def save_output_to_file(output_box):
    """
    Save the contents of the output box to a user-selected file.
    
    Args:
        output_box: ScrolledText widget
    """
    content = output_box.get("1.0", tk.END).rstrip()
    if not content:
        messagebox.showinfo("Save Output", "No output to save.")
        return
    filename = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        initialfile=f"portfolio_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    if filename:
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Save Output", f"Output saved to {filename}")
        except Exception as e:
            messagebox.showerror("Save Output", f"Failed to save file: {e}")


def on_closing(root):
    """
    Prompt to save output on exit, then close the GUI.
    
    Args:
        root: Tkinter root window
    """
    if messagebox.askyesno("Save", "Save output to file before exiting?"):
        # This will be handled by the main loop
        pass
    root.destroy()


def setup_keyboard_shortcuts(root, output_box):
    """
    Set up keyboard shortcuts.
    
    Args:
        root: Tkinter root window
        output_box: ScrolledText widget
    """
    root.bind_all("<Control-s>", lambda event: save_output_to_file(output_box))
