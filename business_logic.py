"""Business logic for investment calculations and analysis."""

import yfinance as yf
from constants import investments, CASH_CAD, CASH_USD, FUTURE, currency_ticker

# Global variables for tracking totals
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


def get_currency_conversion(ticker: str) -> float:
    """Get currency conversion rate for given ticker."""
    dat = yf.Ticker(ticker)
    info = dat.get_fast_info()
    value = info.last_price
    gui_print(f"Currency {ticker} = ${value:,.2f}")
    return value


def accumulate_weighted_average(investment, value):
    """Add to weighted average accumulation."""
    global weighted_average_accumulated
    weighted_average_accumulated += value * investment["LTReturn"]


def calculated_and_show_investment(investment, usdcad_rate: float) -> tuple:
    """
    Calculate investment value and display details.
    
    Args:
        investment: Investment dict with Ticker, Quantity, Currency, etc.
        usdcad_rate: Current USD to CAD exchange rate
        
    Returns:
        Tuple of (value in CAD, investment type)
    """
    global investment_list
    
    if investment["Ticker"] != "":
        dat = yf.Ticker(investment["Ticker"])
        basic_info = dat.get_fast_info()
        value = basic_info.last_price * investment["Quantity"]

        if investment["Currency"] == "USD":
            value = value * usdcad_rate
        valueUSD = value / usdcad_rate
        gui_print(f'{investment["Name"]} {investment["Ticker"]}: Price: ${basic_info.last_price:,.2f} {investment["Currency"]}: Market Value=${value:,.2f} CAD (${valueUSD:,.2f} USD)')

    investment_list[investment["Ticker"]] = (investment["ExpenseRatio"], value)
    accumulate_weighted_average(investment, value)

    return value, investment["Type"]


def process_investments(investment_list_input, usdcad_rate: float):
    """
    Process all investments and calculate totals.
    
    Args:
        investment_list_input: List of investment dicts from constants
        usdcad_rate: Current USD to CAD exchange rate
        
    Returns:
        Dict with calculated totals
    """
    global total_intl_stock, total_domestic_stock, total_canadian_stock
    global total_bond, total_cash, tot_cad, expense_ratio_net, investment_expense
    
    for investment in investment_list_input:
        value, inv_type = calculated_and_show_investment(investment, usdcad_rate)
        
        if inv_type == "StockI":
            total_intl_stock += value
        elif inv_type == "StockD":
            total_domestic_stock += value
        elif inv_type == "StockC":
            total_canadian_stock += value
        elif inv_type == "Bond":
            total_bond += value
        elif inv_type == "Cash":
            total_cash += value
        else:
            gui_print(f"Unknown investment type: {inv_type}")
        tot_cad += value

    gui_print(f'\n\nCash = ${CASH_CAD:,.2f} CAD')
    gui_print(f'Cash = ${CASH_USD:,.2f} USD')

    total_cash = CASH_CAD + (CASH_USD * usdcad_rate)
    tot_cad += CASH_CAD
    tot_cad += CASH_USD * usdcad_rate

    if use_future:
        tot_cad += FUTURE

    # Calculate expense ratios
    for ticker in investment_list:
        expense_ratio, value = investment_list[ticker]
        if ticker != "":
            investment_expense += value * expense_ratio / 100
            expense_ratio_net += value * expense_ratio / tot_cad
            gui_print(f'{ticker}: ${value:,.2f} : {expense_ratio:,.2f}%')

    return {
        'tot_cad': tot_cad,
        'total_cash': total_cash,
        'total_intl_stock': total_intl_stock,
        'total_domestic_stock': total_domestic_stock,
        'total_canadian_stock': total_canadian_stock,
        'total_bond': total_bond,
        'investment_expense': investment_expense,
        'expense_ratio_net': expense_ratio_net,
        'weighted_average': weighted_average_accumulated,
    }


def calculate_projection_values(tot_cad_val: float, expense_ratio: float) -> dict:
    """
    Calculate projection values at various percentages.
    
    Args:
        tot_cad_val: Total value in CAD
        expense_ratio: Expense ratio as percentage
        
    Returns:
        Dict with projection values
    """
    two_percent = tot_cad_val * 0.02
    two_point_five_percent = tot_cad_val * 0.025
    three_percent = tot_cad_val * 0.03
    three_point_five_percent = tot_cad_val * 0.035
    four_percent = tot_cad_val * 0.04
    one_twenty_five_k = 125000 / tot_cad_val * 100 + expense_ratio

    return {
        '2%': two_percent,
        '2.5%': two_point_five_percent,
        '3%': three_percent,
        '3.5%': three_point_five_percent,
        '4%': four_percent,
        '125k': one_twenty_five_k,
    }


def calculate_projection_values_80_percent(tot_cad_val: float, expense_ratio: float) -> dict:
    """Calculate projection values for 80% of total."""
    eighty_percent_value = tot_cad_val * 0.80
    one_twenty_five_k_80 = 125000 / eighty_percent_value * 100 + expense_ratio
    two_point_five_percent_80 = eighty_percent_value * 0.025
    three_percent_80 = eighty_percent_value * 0.03
    three_point_five_percent_80 = eighty_percent_value * 0.035
    four_percent_80 = eighty_percent_value * 0.04

    return {
        '80%': eighty_percent_value,
        '2.5%': two_point_five_percent_80,
        '3%': three_percent_80,
        '3.5%': three_point_five_percent_80,
        '4%': four_percent_80,
        '125k': one_twenty_five_k_80,
    }


def print_investment_summary(portfolio_data: dict):
    """
    Print comprehensive investment summary including totals, allocations, and projections.
    
    Args:
        portfolio_data: Dict with portfolio totals and calculations
    """
    # Investment totals and expenses
    gui_print(f'\n\nInvestment Expense = ${portfolio_data["investment_expense"]:,.2f} CAD')
    gui_print(f'Net Expense Ratio = {portfolio_data["expense_ratio_net"]:,.2f}%')
    gui_print(f'\n\nTotal Investments = {portfolio_data["tot_cad"]:,.2f} CAD\n\n')
    
    # Allocation breakdown
    gui_print(f'Total Cash = {portfolio_data["total_cash"]:,.2f} CAD : %Cash = {portfolio_data["total_cash"]/portfolio_data["tot_cad"] *100:,.2f}%')
    gui_print(f'Total International Stock = {portfolio_data["total_intl_stock"]:,.2f} CAD : %Intl = {portfolio_data["total_intl_stock"]/portfolio_data["tot_cad"] *100:,.2f}%')
    gui_print(f'Total Canadian Stock = {portfolio_data["total_canadian_stock"]:,.2f} CAD :  %Canada = {portfolio_data["total_canadian_stock"]/portfolio_data["tot_cad"] *100:,.2f}%')
    gui_print(f'Total US Stock = {portfolio_data["total_domestic_stock"]:,.2f} CAD :  %US = {portfolio_data["total_domestic_stock"]/portfolio_data["tot_cad"] *100:,.2f}%')
    gui_print(f'Total Bond = {portfolio_data["total_bond"]:,.2f} CAD : %Bond = {portfolio_data["total_bond"]/portfolio_data["tot_cad"] *100:,.2f}%')
    
    # Percentage-based projections (100% allocation)
    gui_print(f'\n2.0% of Total = ${portfolio_data["tot_cad"] * 0.02:,.2f} CAD')
    gui_print(f'2.5% of Total = ${portfolio_data["tot_cad"] * 0.025:,.2f} CAD')
    gui_print(f'3.0% of Total = ${portfolio_data["tot_cad"] * 0.03:,.2f} CAD')
    gui_print(f'3.5% of Total = ${portfolio_data["tot_cad"] * 0.035:,.2f} CAD')
    gui_print(f'4.0% of Total = ${portfolio_data["tot_cad"] * 0.04:,.2f} CAD')
    
    # 125k calculations
    one_twenty_five_k = 125000 / portfolio_data["tot_cad"] * 100 + portfolio_data["expense_ratio_net"]
    gui_print(f'125k with investment expenses = {one_twenty_five_k:,.2f}')
    
    # Weighted average return
    gui_print(f'\n\nTotal Expected Weighted Average Return of Investments = {portfolio_data["weighted_average"]/portfolio_data["tot_cad"]*100.:,.2f}%')
    
    # Percentage-based projections (80% allocation)
    eighty_percent_value = portfolio_data["tot_cad"] * 0.80
    one_twenty_five_k_80 = 125000 / eighty_percent_value * 100 + portfolio_data["expense_ratio_net"]
    
    gui_print(f'\n80% of Total = ${eighty_percent_value:,.2f} CAD')
    gui_print(f'2.5% of Total = ${eighty_percent_value * 0.025:,.2f} CAD')
    gui_print(f'3.0% of Total = ${eighty_percent_value * 0.03:,.2f} CAD')
    gui_print(f'3.5% of Total = ${eighty_percent_value * 0.035:,.2f} CAD')
    gui_print(f'4.0% of Total = ${eighty_percent_value * 0.04:,.2f} CAD')
    gui_print(f'125k with investment expenses = {one_twenty_five_k_80:,.2f}')
