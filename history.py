"""History tracking and portfolio performance analysis."""

import os
import re
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter

from charts import _attach_hover_tooltip

# Reference to gui_print function (will be set by main)
gui_print_func = None


def set_gui_print(func):
    """Set the gui_print function reference."""
    global gui_print_func
    gui_print_func = func


def gui_print(msg):
    """Wrapper for gui_print_func."""
    if gui_print_func:
        gui_print_func(msg)
    else:
        print(msg)


def load_portfolio_history(directory: str) -> list:
    """
    Load all portfolio output files from directory.
    
    Args:
        directory: Path to directory containing portfolio_output_*.txt files
        
    Returns:
        List of tuples (datetime, value) sorted by date
    """
    pattern = r'portfolio_output_(\d{8}_\d{6})\.txt'
    data = []
    
    for filename in os.listdir(directory):
        match = re.match(pattern, filename)
        if match:
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match_value = re.search(r'Total Investments = ([0-9,]+\.[0-9]{2})', content)
                    if match_value:
                        value_str = match_value.group(1).replace(',', '')
                        value = float(value_str)
                        date_str = match.group(1)
                        date_obj = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                        data.append((date_obj, value))
            except Exception as e:
                gui_print(f"Error reading {filename}: {e}")
    
    data.sort(key=lambda x: x[0])
    return data


def load_and_plot_investment_history(root, directory: str = None):
    """
    Load and plot investment history over time.
    
    Args:
        root: Tkinter root window
        directory: Path to portfolio files (uses default if None)
    """
    if directory is None:
        directory = r'C:\\Personal\\personal\\Finance and Taxes\\investment_saves'
    
    if not directory or not os.path.exists(directory):
        messagebox.showerror("Error", f"Directory not found: {directory}")
        return
    
    data = load_portfolio_history(directory)
    
    if not data:
        messagebox.showinfo("No Data", "No portfolio output files found.")
        return
    
    dates = [item[0] for item in data]
    values = [item[1] for item in data]
    
    # Calculate percentage gains
    initial_value = values[0]
    gains = [(v - initial_value) / initial_value * 100 for v in values]
    gain_lookup = {dates[i]: gains[i] for i in range(len(dates))}

    # Create segments for percentage gain coloring
    segments = []
    current_segment = {'dates': [], 'gains': [], 'color': None}
    for i in range(len(gains)):
        color = 'green' if gains[i] >= 0 else 'red'
        if current_segment['color'] != color:
            if current_segment['dates']:
                segments.append(current_segment)
            current_segment = {'dates': [dates[i]], 'gains': [gains[i]], 'color': color}
        else:
            current_segment['dates'].append(dates[i])
            current_segment['gains'].append(gains[i])
    if current_segment['dates']:
        segments.append(current_segment)
    
    # Create a new window for the chart
    new_window = tk.Toplevel(root)
    new_window.title("Investment History")
    new_window.geometry("1000x600")
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    line, = ax.plot(dates, values, marker='o', linestyle='-', linewidth=2, markersize=6, label='Total Investments')
    line.set_picker(8)
    ax.set_ylabel("Total Investments (CAD)", fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Format y-axis to show values with commas and currency
    def currency_formatter(x, _):
        if x >= 1e6:
            return f'${x/1e6:,.3f}M'
        else:
            return f'${x/1e3:,.0f}K'
    
    ax.yaxis.set_major_formatter(FuncFormatter(currency_formatter))
    
    # Second y-axis for percentage gain
    ax2 = ax.twinx()
    for i, segment in enumerate(segments):
        label = 'Percentage Gain' if i == 0 else None
        ax2.plot(segment['dates'], segment['gains'], linestyle='-', color=segment['color'], linewidth=2, label=label)
    ax2.set_ylabel("Percentage Gain (%)", fontsize=12, color='black')
    ax2.tick_params(axis='y', labelcolor='black')
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.1f}%'))
    
    # Add legend
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # Rotate x-axis labels for better readability
    fig.autofmt_xdate(rotation=45, ha='right')
    
    # Embed the figure in the new window
    canvas = FigureCanvasTkAgg(fig, master=new_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def format_history_tooltip(x, y, artist):
        if isinstance(x, datetime):
            x_text = x.strftime('%Y-%m-%d %H:%M:%S')
            gain = gain_lookup.get(x, None)
        else:
            x_text = str(x)
            gain = None
        gain_text = f"\nPercentage Gain: {gain:.2f}%" if gain is not None else ""
        return f"{x_text}\nTotal Value: ${y:,.2f} CAD{gain_text}"

    _attach_hover_tooltip(canvas, ax, [line], format_history_tooltip)

    gui_print(f"Change: ${max(values) - min(values):,.2f} CAD ({(max(values) - min(values))/min(values)*100:,.2f}%)")


def load_individual_investment_history(directory: str) -> dict:
    """
    Load individual investment performance data from history files.
    
    Args:
        directory: Path to portfolio files
        
    Returns:
        Dict mapping investment names with tickers to list of (datetime, value) tuples
    """
    pattern = r'portfolio_output_(\d{8}_\d{6})\.txt'
    data_by_investment = {}
    
    for filename in os.listdir(directory):
        match = re.match(pattern, filename)
        if match:
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    date_str = match.group(1)
                    date_obj = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                    
                    # Extract individual investment values
                    # Pattern: "Investment Name TICKER: ... Market Value=$value CAD"
                    investment_pattern = r'(.+?)\s+([A-Z0-9=\.]+):\s+(?:.*?)Market Value=\$([0-9,]+\.[0-9]{2})\s+CAD'
                    for inv_match in re.finditer(investment_pattern, content):
                        inv_name = inv_match.group(1).strip()
                        inv_ticker = inv_match.group(2).strip()
                        inv_value_str = inv_match.group(3).replace(',', '')
                        inv_value = float(inv_value_str)
                        
                        # Use "Name (TICKER)" as key
                        inv_key = f"{inv_name} ({inv_ticker})"
                        
                        if inv_key not in data_by_investment:
                            data_by_investment[inv_key] = []
                        data_by_investment[inv_key].append((date_obj, inv_value))
            except Exception as e:
                gui_print(f"Error reading {filename}: {e}")
    
    # Sort each investment's data by date
    for inv_name in data_by_investment:
        data_by_investment[inv_name].sort(key=lambda x: x[0])
    
    return data_by_investment


def show_individual_performance(root, directory: str = None):
    """
    Display individual investment performance over time.
    
    Args:
        root: Tkinter root window
        directory: Path to portfolio files (uses default if None)
    """
    if directory is None:
        directory = r'C:\Personal\personal\Finance and Taxes\investment_saves'
    
    if not directory or not os.path.exists(directory):
        messagebox.showerror("Error", f"Directory not found: {directory}")
        return
    
    data_by_investment = load_individual_investment_history(directory)
    
    if not data_by_investment:
        messagebox.showinfo("No Data", "No individual investment data found.")
        return
    
    # Create a new window for charts
    new_window = tk.Toplevel(root)
    new_window.title("Individual Investment Performance")
    new_window.geometry("1200x700")
    
    # Create a frame for controls
    control_frame = tk.Frame(new_window)
    control_frame.pack(pady=5)
    
    tk.Label(control_frame, text="Select Investment:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
    
    # Dropdown to select which investment to view
    selected_inv_var = tk.StringVar(value=list(data_by_investment.keys())[0])
    inv_dropdown = tk.OptionMenu(control_frame, selected_inv_var, *sorted(data_by_investment.keys()))
    inv_dropdown.pack(side=tk.LEFT, padx=5)
    
    # Canvas holder for redraw
    canvas_holder = {'canvas': None}
    
    def draw_investment_chart():
        # Remove old chart if exists
        if canvas_holder['canvas'] is not None:
            canvas_holder['canvas'].get_tk_widget().destroy()
        
        inv_name = selected_inv_var.get()
        data = data_by_investment[inv_name]
        
        if not data:
            return
        
        dates = [item[0] for item in data]
        values = [item[1] for item in data]
        
        # Calculate percentage gains
        initial_value = values[0]
        gains = [(v - initial_value) / initial_value * 100 for v in values]
        gain_lookup = {dates[i]: gains[i] for i in range(len(dates))}

        # Create segments for percentage gain coloring (green/red)
        segments = []
        current_segment = {'dates': [], 'gains': [], 'color': None}
        for i in range(len(gains)):
            color = 'green' if gains[i] >= 0 else 'red'
            if current_segment['color'] != color:
                if current_segment['dates']:
                    segments.append(current_segment)
                current_segment = {'dates': [dates[i]], 'gains': [gains[i]], 'color': color}
            else:
                current_segment['dates'].append(dates[i])
                current_segment['gains'].append(gains[i])
        if current_segment['dates']:
            segments.append(current_segment)
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 6))
        line, = ax.plot(dates, values, marker='o', linestyle='-', linewidth=2, markersize=6, label=inv_name)
        line.set_picker(8)
        ax.set_title(f"{inv_name} - Performance Over Time with Percentage Gain", fontsize=14, fontweight='bold')
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Investment Value (CAD)", fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Format y-axis to show values with commas and currency
        def currency_formatter(x, _):
            if x >= 1e6:
                return f'${x/1e6:,.3f}M'
            else:
                return f'${x/1e3:,.0f}K'
        
        ax.yaxis.set_major_formatter(FuncFormatter(currency_formatter))
        
        # Second y-axis for percentage gain
        ax2 = ax.twinx()
        for i, segment in enumerate(segments):
            label = 'Percentage Gain' if i == 0 else None
            ax2.plot(segment['dates'], segment['gains'], linestyle='-', color=segment['color'], linewidth=2, label=label)
        ax2.set_ylabel("Percentage Gain (%)", fontsize=12, color='black')
        ax2.tick_params(axis='y', labelcolor='black')
        ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.1f}%'))
        
        # Add legend
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Rotate x-axis labels for better readability
        fig.autofmt_xdate(rotation=45, ha='right')
        
        # Embed the figure
        canvas_holder['canvas'] = FigureCanvasTkAgg(fig, master=new_window)
        canvas_holder['canvas'].draw()
        canvas_holder['canvas'].get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def format_individual_tooltip(x, y, artist):
            if isinstance(x, datetime):
                x_text = x.strftime('%Y-%m-%d %H:%M:%S')
                gain = gain_lookup.get(x, None)
            else:
                x_text = str(x)
                gain = None
            gain_text = f"\nPercentage Gain: {gain:.2f}%" if gain is not None else ""
            return f"{inv_name}\n{x_text}\nValue: ${y:,.2f} CAD{gain_text}"

        _attach_hover_tooltip(canvas_holder['canvas'], ax, [line], format_individual_tooltip)
    
    # Bind dropdown change to redraw
    selected_inv_var.trace('w', lambda *args: draw_investment_chart())
    draw_investment_chart()
    
    # Initial draw
    draw_investment_chart()
