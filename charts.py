"""Chart generation and visualization functions."""

import os
import re
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import numpy as np
import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter

# Reference to gui_print function (will be set by main)
gui_print_func = None

def _create_tooltip_annotation(ax):
    annot = ax.annotate(
        "",
        xy=(0, 0),
        xytext=(15, 15),
        textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.4", fc="yellow", alpha=0.9),
        arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0")
    )
    annot.set_visible(False)
    return annot


def _attach_hover_tooltip(canvas, ax, artists, formatter):
    annot = _create_tooltip_annotation(ax)
    fig = ax.figure
    pixel_tolerance = 8

    def hover(event):
        if event.inaxes is None:
            if annot.get_visible():
                annot.set_visible(False)
                canvas.draw_idle()
            return

        hit = False
        for artist in artists:
            if isinstance(artist, mpl.container.BarContainer):
                for bar in artist:
                    contains, _ = bar.contains(event)
                    if contains:
                        x = bar.get_x() + bar.get_width() / 2
                        y = bar.get_height()
                        text = formatter(x, y, bar)
                        annot.xy = (x, y)
                        annot.set_text(text)
                        annot.set_visible(True)
                        hit = True
                        break
                if hit:
                    break

            elif isinstance(artist, mpl.lines.Line2D):
                contains, ind = artist.contains(event)
                xdata = np.asarray(artist.get_xdata())
                ydata = np.asarray(artist.get_ydata())
                idx = None
                ind_values = ind.get("ind")
                if contains and ind_values is not None and len(ind_values) > 0:
                    idx = ind_values[0]
                else:
                    if xdata.dtype.kind in ('M', 'O'):
                        xdata_num = mdates.date2num(xdata)
                    else:
                        xdata_num = xdata.astype(float)
                    ydata_num = ydata.astype(float)
                    xy_pixels = ax.transData.transform(np.column_stack([xdata_num, ydata_num]))
                    dx = np.abs(xy_pixels[:, 0] - event.x)
                    dy = np.abs(xy_pixels[:, 1] - event.y)
                    dist = np.hypot(dx, dy)
                    idx = np.argmin(dist)
                    if dist[idx] > pixel_tolerance:
                        idx = None
                if idx is not None:
                    x = xdata[idx]
                    y = ydata[idx]
                    text = formatter(x, y, artist)
                    annot.xy = (x, y)
                    annot.set_text(text)
                    annot.set_visible(True)
                    hit = True
                    break

        if not hit and annot.get_visible():
            annot.set_visible(False)
            canvas.draw_idle()
        elif hit:
            canvas.draw_idle()

    canvas.mpl_connect("motion_notify_event", hover)


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


def draw_allocation_chart(root, portfolio_data: dict):
    """
    Draw asset allocation pie chart in a new popup window.
    
    Args:
        root: Tkinter root window
        portfolio_data: Dict with portfolio totals (total_cash, total_domestic_stock, etc.)
    """
    new_window = tk.Toplevel(root)
    new_window.title("Asset Allocation")
    new_window.geometry("600x600")
    
    labels = ["Cash", "US Stock", "Canadian Stock", "International Stock", "Bonds"]
    values = [
        portfolio_data['total_cash'],
        portfolio_data['total_domestic_stock'],
        portfolio_data['total_canadian_stock'],
        portfolio_data['total_intl_stock'],
        portfolio_data['total_bond']
    ]
    
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
    ax.set_title("Asset Allocation", fontsize=14, fontweight='bold')
    
    canvas = FigureCanvasTkAgg(fig, master=new_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


def show_future_value_chart(root, portfolio_data: dict):
    """
    Show future value chart in a new popup window with input options.
    
    Args:
        root: Tkinter root window
        portfolio_data: Dict with portfolio totals and weighted average
    """
    new_window = tk.Toplevel(root)
    new_window.title("Future Value Projection")
    new_window.geometry("1000x700")
    
    # Frame for years input and redraw button
    years_frame = tk.Frame(new_window)
    years_frame.pack(pady=5)
    
    tk.Label(years_frame, text="Number of Years:").pack(side=tk.LEFT, padx=5)
    years_var = tk.StringVar(value="20")
    years_entry = tk.Entry(years_frame, textvariable=years_var, width=5)
    years_entry.pack(side=tk.LEFT, padx=5)
    
    # Placeholder for canvas so we can destroy it before redraw
    canvas_holder = {'canvas': None}
    
    def draw_future_value_chart_impl():
        # Remove old chart if exists
        if canvas_holder['canvas'] is not None:
            canvas_holder['canvas'].get_tk_widget().destroy()

        try:
            num_years = int(years_var.get())
        except ValueError:
            num_years = 20  # fallback

        current_year = datetime.now().year
        years = np.arange(current_year, current_year + num_years)
        initial_value = portfolio_data['tot_cad']
        annual_return = portfolio_data['weighted_average'] / portfolio_data['tot_cad']

        future_values = initial_value * (1 + annual_return) ** (years - current_year)
        pessimistic_return = annual_return - 0.03

        # Consumption + inflation
        annual_consumption = initial_value * 0.025
        future_values_consumption = []
        value = initial_value
        future_values_consumption.append(value)
        for i in range(len(years) - 1):
            value = value * (1 + annual_return) - annual_consumption
            future_values_consumption.append(value)
            annual_consumption *= 1.03

        # Pessimistic scenario
        annual_consumption_pessimistic = initial_value * 0.025
        future_values_consumption_pessimistic = []
        value_pessimistic = initial_value
        future_values_consumption_pessimistic.append(value_pessimistic)
        for i in range(len(years) - 1):
            value_pessimistic = value_pessimistic * (1 + pessimistic_return) - annual_consumption_pessimistic
            future_values_consumption_pessimistic.append(value_pessimistic)
            annual_consumption_pessimistic *= 1.03

        fig2, ax2 = plt.subplots(figsize=(12, 8))
        line_no_consumption, = ax2.plot(years, future_values, marker='o', label='No Consumption')
        line_consumption, = ax2.plot(years, future_values_consumption, marker='x', linestyle='--', color='red', label='2.5% Consumption + 3% Inflation')
        line_pessimistic, = ax2.plot(years, future_values_consumption_pessimistic, marker='x', linestyle=':', color='orange', label='2.5% Consumption + 3% Inflation (Pessimistic)')
        ax2.set_title("Projected Future Value of Investments", fontsize=14, fontweight='bold')
        ax2.set_xlabel("Years", fontsize=12)
        ax2.set_ylabel("Portfolio Value (CAD)", fontsize=12)
        ax2.grid(True, alpha=0.3)
        formatter = FuncFormatter(lambda x, _: f'${x/1e6:,.1f}M')
        ax2.yaxis.set_major_formatter(formatter)
        ax2.legend()

        for line in (line_no_consumption, line_consumption, line_pessimistic):
            line.set_picker(5)

        canvas_holder['canvas'] = FigureCanvasTkAgg(fig2, master=new_window)
        canvas_holder['canvas'].draw()
        canvas_holder['canvas'].get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def format_future_value_tooltip(x, y, artist):
            return f"Year: {int(x)}\nValue: ${y:,.0f} CAD"

        _attach_hover_tooltip(canvas_holder['canvas'], ax2, [line_no_consumption, line_consumption, line_pessimistic], format_future_value_tooltip)
    
    redraw_button = tk.Button(years_frame, text="Redraw Chart", command=draw_future_value_chart_impl)
    redraw_button.pack(side=tk.LEFT, padx=5)
    
    # Initial draw
    draw_future_value_chart_impl()


def show_annual_expense_predictor(root, portfolio_data: dict):
    """
    Show annual expense capacity projections in a new popup window.

    Args:
        root: Tkinter root window
        portfolio_data: Dict with portfolio totals and calculations
    """
    new_window = tk.Toplevel(root)
    new_window.title("Annual Expense Capacity")
    new_window.geometry("900x700")

    tot_cad = portfolio_data.get('tot_cad', 0)
    expense_ratio_net = portfolio_data.get('expense_ratio_net', 0)
    if tot_cad == 0:
        messagebox.showerror("Data Error", "Portfolio total value is zero or unavailable.")
        new_window.destroy()
        return

    labels = ["2.0%", "2.5%", "3.0%", "3.5%", "4.0%"]
    values = [tot_cad * pct for pct in [0.02, 0.025, 0.03, 0.035, 0.04]]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(labels, values, color=["#4c72b0", "#55a868", "#c44e52", "#8172b3", "#ccb974"])
    ax.set_title("Annual Expense Capacity from Total Portfolio", fontsize=14, fontweight='bold')
    ax.set_xlabel("Withdrawal Rate", fontsize=12)
    ax.set_ylabel("Annual CAD Capacity", fontsize=12)
    ax.grid(axis='y', alpha=0.3)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x/1e3:,.0f}k'))

    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'${height/1e3:,.1f}k',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 6),
                    textcoords='offset points',
                    ha='center', va='bottom', fontsize=10)

    canvas = FigureCanvasTkAgg(fig, master=new_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def format_expense_tooltip(x, y, artist):
        label = artist.get_label() if hasattr(artist, 'get_label') else ''
        return f"{label}\nAnnual Capacity: ${y:,.0f} CAD"

    _attach_hover_tooltip(canvas, ax, [bars], format_expense_tooltip)

    summary_frame = tk.Frame(new_window)
    summary_frame.pack(fill=tk.X, padx=10, pady=10)

    annual_125k = 125000 / tot_cad * 100 + expense_ratio_net
    summary_text = (
        f"Total Portfolio Value: ${tot_cad:,.2f} CAD\n"
        f"Net Expense Ratio: {expense_ratio_net:,.2f}%\n"
        f"125k with investment expenses metric: {annual_125k:,.2f}\n"
        f"\nUse these rates as a guide to annual spending capacity based on your current portfolio."
    )

    summary_label = tk.Label(summary_frame, text=summary_text, justify=tk.LEFT, font=("Helvetica", 11))
    summary_label.pack(fill=tk.X)


def show_swr_trends(root):
    """
    Show Safe Withdrawal Rate trends over time based on historical data.
    
    Args:
        root: Tkinter root window
    """
    new_window = tk.Toplevel(root)
    new_window.title("SWR Trends")
    new_window.geometry("1000x700")
    
    # Load historical data
    directory = r'C:\Personal\personal\Finance and Taxes\investment_saves'
    
    pattern = r'portfolio_output_(\d{8}_\d{6})\.txt'
    data = []
    
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            match = re.match(pattern, filename)
            if match:
                filepath = os.path.join(directory, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract "125k with investment expenses" value
                        match_swr = re.search(r'125k with investment expenses = ([0-9,]+\.[0-9]{2})', content)
                        if match_swr:
                            swr_value_str = match_swr.group(1).replace(',', '')
                            swr_value = float(swr_value_str)
                            date_str = match.group(1)
                            date_obj = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                            data.append((date_obj, swr_value))
                except Exception as e:
                    gui_print(f"Error reading {filename}: {e}")
    
    if not data:
        messagebox.showerror("No Data", f"No SWR data found in {directory}")
        new_window.destroy()
        return
    
    # Sort by date
    data.sort(key=lambda x: x[0])
    dates = [item[0] for item in data]
    swr_values = [item[1] for item in data]
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    line, = ax.plot(dates, swr_values, marker='o', linestyle='-', linewidth=2, markersize=6, 
           color='blue', label='Safe Withdrawal Rate (%)')
    
    ax.set_title("Safe Withdrawal Rate Trends Over Time", fontsize=14, fontweight='bold')
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Safe Withdrawal Rate (%)", fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Format y-axis to show percentages
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.2f}%'))
    
    # Add horizontal reference lines for common SWR guidelines
    ax.axhline(y=4.0, color='red', linestyle='--', alpha=0.7, label='4% Rule')
    ax.axhline(y=3.0, color='orange', linestyle='--', alpha=0.7, label='3% Rule')
    
    ax.legend(loc='upper left', fontsize=10)
    
    # Rotate x-axis labels for better readability
    fig.autofmt_xdate(rotation=45, ha='right')
    
    line.set_picker(5)

    # Embed the figure
    canvas = FigureCanvasTkAgg(fig, master=new_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def format_swr_tooltip(x, y, artist):
        if isinstance(x, datetime):
            date_str = x.strftime('%Y-%m-%d')
        else:
            date_str = str(x)
        return f"{date_str}\nSWR: {y:.2f}%"

    _attach_hover_tooltip(canvas, ax, [line], format_swr_tooltip)
    
    # Print summary statistics
    current_swr = swr_values[-1] if swr_values else 0
    min_swr = min(swr_values) if swr_values else 0
    max_swr = max(swr_values) if swr_values else 0
    avg_swr = sum(swr_values) / len(swr_values) if swr_values else 0
    
    gui_print(f"\n\nSWR Trends Summary:")
    gui_print(f"Current SWR: {current_swr:.2f}%")
    gui_print(f"Minimum SWR: {min_swr:.2f}%")
    gui_print(f"Maximum SWR: {max_swr:.2f}%")
    gui_print(f"Average SWR: {avg_swr:.2f}%")
    gui_print(f"Data points: {len(data)}")
