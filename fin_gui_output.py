import yfinance as yf
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, filedialog, messagebox
import numpy as np
import os
import re

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt


from constants import (
    investments, CASH_CAD, CASH_USD, FUTURE, currency_ticker
)

tot_cad = 0
weighted_average_accumulated = 0
use_future = False
total_intl_stock = 0
total_domestic_stock = 0
total_canadian_stock = 0
total_bond = 0
total_cash = 0
expense_ratio_net = 0
investment_expense = 0
investment_list = {}

# ---------------------------
# GUI setup
# ---------------------------
root = tk.Tk()
root.title("Investment Portfolio Summary")
root.geometry("800x600")

# Button frame for horizontal layout
button_frame = tk.Frame(root)
button_frame.pack(pady=5)

save_button = tk.Button(button_frame, text="Save Output", command= lambda: save_output_to_file())
save_button.pack(side=tk.LEFT, padx=5)

history_button = tk.Button(button_frame, text="View Investment History", command=lambda: load_and_plot_investment_history())
history_button.pack(side=tk.LEFT, padx=5)

allocation_button = tk.Button(button_frame, text="Asset Allocation Chart", command=lambda: draw_allocation_chart())
allocation_button.pack(side=tk.LEFT, padx=5)

future_value_button = tk.Button(button_frame, text="View Future Value Chart", command=lambda: show_future_value_chart())
future_value_button.pack(side=tk.LEFT, padx=5)

output_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Courier New", 10))
output_box.pack(expand=True, fill="both")

def gui_print(msg):
    output_box.insert(tk.END, msg + "\n")
    output_box.see(tk.END)


def save_output_to_file():
    """Save the contents of the output box to a user-selected file."""
    content = output_box.get("1.0", tk.END).rstrip()
    if not content:
        messagebox.showinfo("Save Output", "No output to save.")
        return
    filename = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files","*.txt"), ("All files","*.*")],
        initialfile=f"portfolio_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    if filename:
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Save Output", f"Output saved to {filename}")
        except Exception as e:
            messagebox.showerror("Save Output", f"Failed to save file: {e}")


def load_and_plot_investment_history():
    """Load all saved portfolio output files and plot investment value over time."""
    # Ask user to select the directory containing portfolio output files
    # directory = filedialog.askdirectory(title="Select directory containing portfolio output files")
    directory = r'C:\\Personal\\personal\\Finance and Taxes\\investment_saves'
    
    if not directory:
        return
    
    # Find all portfolio_output_*.txt files
    pattern = r'portfolio_output_(\d{8}_\d{6})\.txt'
    data = []
    
    for filename in os.listdir(directory):
        match = re.match(pattern, filename)
        if match:
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract "Total Investments" value
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
        messagebox.showinfo("No Data", "No portfolio output files found.")
        return
    
    # Sort by date
    data.sort(key=lambda x: x[0])
    dates = [item[0] for item in data]
    values = [item[1] for item in data]
    
    # Calculate percentage gains
    initial_value = values[0]
    gains = [(v - initial_value) / initial_value * 100 for v in values]
    
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
    ax.plot(dates, values, marker='o', linestyle='-', linewidth=2, markersize=6, label='Total Investments')
    ax.set_title("Total Investments Over Time with Percentage Gain", fontsize=14, fontweight='bold')
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Total Investments (CAD)", fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Format y-axis to show values with commas and currency
    def currency_formatter(x, _):
        if x >= 1e6:
            return f'${x/1e6:,.3f}M'
        else:
            return f'${x/1e3:,.0sf}K'
    
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
    
    # Print summary to output box
    gui_print(f"\n\nLoaded {len(data)} historical records")
    gui_print(f"Date range: {dates[0].strftime('%Y-%m-%d %H:%M:%S')} to {dates[-1].strftime('%Y-%m-%d %H:%M:%S')}")
    gui_print(f"Min value: ${min(values):,.2f} CAD")
    gui_print(f"Max value: ${max(values):,.2f} CAD")
    gui_print(f"Change: ${max(values) - min(values):,.2f} CAD ({(max(values) - min(values))/min(values)*100:,.2f}%)")


def on_closing():
    """Prompt to save output on exit, then close the GUI."""
    if messagebox.askyesno("Save", "Save output to file before exiting?"):
        save_output_to_file()
    root.destroy()

# bind Ctrl+S to save
root.bind_all("<Control-s>", lambda event: save_output_to_file())


# ---------------------------
# Business logic
# ---------------------------
def calculated_and_show_investment(investment) -> float:
    '''
    shows details of the investment and returns the total value
    '''
    if investment["Ticker"] != "":
        dat = yf.Ticker(investment["Ticker"])
        basic_info = dat.get_fast_info()
        value = basic_info.last_price * investment["Quantity"]

        if investment["Currency"] == "USD":
            value = value * USDCAD
        valueUSD = value / USDCAD
        gui_print(f'{investment["Name"]} {investment["Ticker"]}: Price: ${basic_info.last_price:,.2f} {investment["Currency"]}: Market Value=${value:,.2f} CAD (${valueUSD:,.2f} USD)')

    investment_list[investment["Ticker"]] = (investment["ExpenseRatio"], value)
    accumulate_weighted_average(investment, value)

    return value, investment["Type"]

def get_currency_conversion(ticker) -> float:
    dat = yf.Ticker(ticker)
    info = dat.get_fast_info()
    value = info.last_price
    gui_print(f"Currency {ticker} = ${value:,.2f}")
    return value

def accumulate_weighted_average(investment, value):
    global weighted_average_accumulated
    weighted_average_accumulated += value * investment["LTReturn"]

# ---------------------------
# Main calculations
# ---------------------------
USDCAD = get_currency_conversion(currency_ticker)

def process_investments(investments):
    global total_intl_stock, total_domestic_stock, total_canadian_stock, total_bond, total_cash, tot_cad
    for investment in investments:
        value, type = calculated_and_show_investment(investment)
        if type == "StockI":
            total_intl_stock += value
        elif type == "StockD":
            total_domestic_stock += value
        elif type == "StockC":
            total_canadian_stock += value
        elif type == "Bond":
            total_bond += value
        elif type == "Cash":
            total_cash += value
        else:
            gui_print(f"Unknown investment type: {type}")
        tot_cad += value

process_investments(investments)

gui_print(f'\n\nCash = ${CASH_CAD:,.2f} CAD')
gui_print(f'Cash = ${CASH_USD:,.2f} USD')

total_cash = CASH_CAD + (CASH_USD * USDCAD)
tot_cad += CASH_CAD
tot_cad += CASH_USD * USDCAD

if use_future:
    tot_cad += FUTURE

# global investment_expense, expense_ratio_net
for ticker in investment_list:
    expense_ratio, value = investment_list[ticker]
    if ticker != "":
        investment_expense += value * expense_ratio / 100
        expense_ratio_net += value * expense_ratio / tot_cad
        gui_print(f'{ticker}: ${value:,.2f} : {expense_ratio:,.2f}%')

gui_print(f'\n\nInvestment Expense = ${investment_expense:,.2f} CAD')
gui_print(f'Net Expense Ratio = {expense_ratio_net:,.2f}%')
gui_print(f'\n\nTotal Investments = {tot_cad:,.2f} CAD\n\n')
gui_print(f'Total Cash = {total_cash:,.2f} CAD : %Cash = {total_cash/tot_cad *100:,.2f}%')
gui_print(f'Total International Stock = {total_intl_stock:,.2f} CAD : %Intl = {total_intl_stock/tot_cad *100:,.2f}%')
gui_print(f'Total Canadian Stock = {total_canadian_stock:,.2f} CAD :  %Canada = {total_canadian_stock/tot_cad *100:,.2f}%')
gui_print(f'Total US Stock = {total_domestic_stock:,.2f} CAD :  %US = {total_domestic_stock/tot_cad *100:,.2f}%')
gui_print(f'Total Bond = {total_bond:,.2f} CAD : %Bond = {total_bond/tot_cad *100:,.2f}%')

twopercent_value = tot_cad * .02
twopointfivepercent_value = tot_cad * .025
threepercent_value = tot_cad * .03
threepointfivepercent_value = tot_cad * .035
fourpercent_value = tot_cad * .04

onetwentyfivek = 125000 / tot_cad * 100 + expense_ratio_net
gui_print(f'2.0% of Total = ${twopercent_value:,.2f} CAD')
gui_print(f'2.5% of Total = ${twopointfivepercent_value:,.2f} CAD')
gui_print(f'3.0% of Total = ${threepercent_value:,.2f} CAD')
gui_print(f'3.5% of Total = ${threepointfivepercent_value:,.2f} CAD')
gui_print(f'4.0% of Total = ${fourpercent_value:,.2f} CAD')
gui_print(f'125k with investment expenses = {onetwentyfivek:,.2f}')

gui_print(f'\n\nTotal Expected Weighted Average Return of Investments = {weighted_average_accumulated/tot_cad*100.:,.2f}%')

eightypercent_value = tot_cad * 0.80
onetwentyfivek_80 = 125000 / eightypercent_value  * 100 + expense_ratio_net
twopointfivepercent_value_80 = eightypercent_value * .025
threepercent_value_80 = eightypercent_value * .03
threepointfivepercent_value_80 = eightypercent_value * .035
fourpercent_value_80 = eightypercent_value * .04

gui_print(f'80% of Total = ${eightypercent_value:,.2f} CAD')
gui_print(f'2.5% of Total = ${twopointfivepercent_value_80:,.2f} CAD')
gui_print(f'3.0% of Total = ${threepercent_value_80:,.2f} CAD')
gui_print(f'3.5% of Total = ${threepointfivepercent_value_80:,.2f} CAD')
gui_print(f'4.0% of Total = ${fourpercent_value_80:,.2f} CAD')
gui_print(f'125k with investment expenses = {onetwentyfivek_80:,.2f}')

# ---------------------------
# Chart Functions (Popup Windows)
# ---------------------------

def draw_allocation_chart():
    """Draw asset allocation pie chart in a new popup window."""
    new_window = tk.Toplevel(root)
    new_window.title("Asset Allocation")
    new_window.geometry("600x600")
    
    labels = ["Cash", "US Stock", "Canadian Stock", "International Stock", "Bonds"]
    values = [total_cash, total_domestic_stock, total_canadian_stock, total_intl_stock, total_bond]
    
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
    ax.set_title("Asset Allocation", fontsize=14, fontweight='bold')
    
    canvas = FigureCanvasTkAgg(fig, master=new_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)



# ---------------------------
# Line Chart for Future Value
# ---------------------------

# Placeholder for canvas so we can destroy it before redraw
canvas2 = None

def show_future_value_chart():
    """Show future value chart in a new popup window with input options."""
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
    
    def draw_future_value_chart():
        # Remove old chart if exists
        if canvas_holder['canvas'] is not None:
            canvas_holder['canvas'].get_tk_widget().destroy()

        try:
            num_years = int(years_var.get())
        except ValueError:
            num_years = 20  # fallback

        current_year = datetime.now().year
        years = np.arange(current_year, current_year + num_years)
        initial_value = tot_cad
        annual_return = weighted_average_accumulated / tot_cad

        future_values = initial_value * (1 + annual_return) ** (years-current_year)
        pessimistic_return = annual_return - 0.03

        # Consumption + inflation
        annual_consumption = initial_value * 0.025
        future_values_consumption = []
        value = initial_value
        future_values_consumption.append(value)
        for i in range(len(years)-1):
            value = value * (1 + annual_return) - annual_consumption
            future_values_consumption.append(value)
            annual_consumption *= 1.03

        # Pessimistic scenario
        annual_consumption_pessimistic = initial_value * 0.025
        future_values_consumption_pessimistic = []
        value_pessimistic = initial_value
        future_values_consumption_pessimistic.append(value_pessimistic)
        for i in range(len(years)-1):
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
    
    redraw_button = tk.Button(years_frame, text="Redraw Chart", command=draw_future_value_chart)
    redraw_button.pack(side=tk.LEFT, padx=5)
    
    # Initial draw
    draw_future_value_chart()

# ---------------------------
# Run GUI
# ---------------------------
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()