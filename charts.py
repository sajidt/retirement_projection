"""Chart generation and visualization functions."""

import os
import re
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter

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
        ax2.plot(years, future_values, marker='o', label='No Consumption')
        ax2.plot(years, future_values_consumption, marker='x', linestyle='--', color='red', label='2.5% Consumption + 3% Inflation')
        ax2.plot(years, future_values_consumption_pessimistic, marker='x', linestyle=':', color='orange', label='2.5% Consumption + 3% Inflation (Pessimistic)')
        ax2.set_title("Projected Future Value of Investments", fontsize=14, fontweight='bold')
        ax2.set_xlabel("Years", fontsize=12)
        ax2.set_ylabel("Portfolio Value (CAD)", fontsize=12)
        ax2.grid(True, alpha=0.3)
        formatter = FuncFormatter(lambda x, _: f'${x/1e6:,.1f}M')
        ax2.yaxis.set_major_formatter(formatter)
        ax2.legend()

        canvas_holder['canvas'] = FigureCanvasTkAgg(fig2, master=new_window)
        canvas_holder['canvas'].draw()
        canvas_holder['canvas'].get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    redraw_button = tk.Button(years_frame, text="Redraw Chart", command=draw_future_value_chart_impl)
    redraw_button.pack(side=tk.LEFT, padx=5)
    
    # Initial draw
    draw_future_value_chart_impl()


def show_annual_expense_predictor(root, portfolio_data: dict):
    """
    Show annual expense capacity based on historical portfolio data.
    Plots what could have been withdrawn at different rates over time.
    
    Args:
        root: Tkinter root window
        portfolio_data: Dict with portfolio totals
    """
    new_window = tk.Toplevel(root)
    new_window.title("Annual Expense Capacity")
    new_window.geometry("1000x700")
    
    # Load historical portfolio data
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
                        match_value = re.search(r'Total Investments = ([0-9,]+\.[0-9]{2})', content)
                        if match_value:
                            value_str = match_value.group(1).replace(',', '')
                            value = float(value_str)
                            date_str = match.group(1)
                            date_obj = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                            data.append((date_obj, value))
                except Exception as e:
                    gui_print(f"Error reading {filename}: {e}")
    
    if not data:
        messagebox.showerror("No Data", f"No portfolio data found in {directory}")
        new_window.destroy()
        return
    
    # Sort by date
    data.sort(key=lambda x: x[0])
    dates = [item[0] for item in data]
    portfolio_values = [item[1] for item in data]
    
    # Calculate withdrawal amounts for each rate
    withdrawal_rates = [0.02, 0.025, 0.03, 0.035, 0.04]
    withdrawals_by_rate = {}
    
    for rate in withdrawal_rates:
        withdrawals_by_rate[rate] = [pv * rate for pv in portfolio_values]
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    colors = ['blue', 'green', 'orange', 'red', 'purple']
    for i, rate in enumerate(withdrawal_rates):
        label = f'{rate*100:.1f}% Withdrawal'
        ax.plot(dates, withdrawals_by_rate[rate], marker='o', linestyle='-', 
               linewidth=2, label=label, color=colors[i])
    
    ax.set_title("Annual Expense Capacity - Historical Withdrawal Capacity Over Time", fontsize=14, fontweight='bold')
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Annual Withdrawal Capacity (CAD)", fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Format y-axis to show currency
    def currency_formatter(x, _):
        if x >= 1e6:
            return f'${x/1e6:,.1f}M'
        else:
            return f'${x/1e3:,.0f}K'
    
    ax.yaxis.set_major_formatter(FuncFormatter(currency_formatter))
    ax.legend(loc='upper left', fontsize=10)
    
    # Rotate x-axis labels for better readability
    fig.autofmt_xdate(rotation=45, ha='right')
    
    # Embed the figure
    canvas = FigureCanvasTkAgg(fig, master=new_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
