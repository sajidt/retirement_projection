"""Main entry point for the Investment Portfolio Summary application."""

import tkinter as tk
from constants import investments, currency_ticker

# Import modules
import gui
import business_logic as bl
import history
import charts


def main():
    """Main application entry point."""
    
    # Create root window
    root = tk.Tk()
    
    # Create GUI
    output_box = gui.create_gui(root)
    
    # Create gui_print wrapper that writes to output_box
    def print_to_gui(msg):
        gui.gui_print(output_box, msg)
    
    # Set gui_print references in all modules
    bl.set_gui_print(print_to_gui)
    history.set_gui_print(print_to_gui)
    charts.set_gui_print(print_to_gui)
    
    # ---------------------------
    # Main calculations
    # ---------------------------
    
    # Get currency conversion
    usdcad = bl.get_currency_conversion(currency_ticker)
    
    # Process investments
    portfolio_data = bl.process_investments(investments, usdcad)
    
    # Print investment summary
    bl.print_investment_summary(portfolio_data)
    
    # ---------------------------
    # Set up callbacks
    # ---------------------------
    
    callbacks = {
        'save_output': lambda: gui.save_output_to_file(output_box),
        'load_history': lambda: history.load_and_plot_investment_history(root),
        'draw_allocation': lambda: charts.draw_allocation_chart(root, portfolio_data),
        'show_future_value': lambda: charts.show_future_value_chart(root, portfolio_data),
        'show_expense_predictor': lambda: charts.show_annual_expense_predictor(root, portfolio_data),
        'show_individual_perf': lambda: history.show_individual_performance(root),
        'show_swr_trends': lambda: charts.show_swr_trends(root),
    }
    
    gui.set_callbacks(callbacks)
    gui.setup_keyboard_shortcuts(root, output_box)
    
    # Set up window closing
    root.protocol("WM_DELETE_WINDOW", lambda: gui.on_closing(root))
    
    # Run GUI
    root.mainloop()


if __name__ == "__main__":
    main()
