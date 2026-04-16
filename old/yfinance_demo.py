import yfinance as yf
from constants import investments, CASH_CAD, CASH_USD, FUTURE, currency_ticker
tot_cad = 0
use_future = False
total_intl_stock = 0
total_domestic_stock = 0
total_canadian_stock = 0
total_bond = 0
total_cash = 0
USDCAD=0
expense_ratio_net = 0
investment_expense = 0
# make a dictionary of investments with ticker as key and the value as a tuple of (value, expense ratio)
investment_list = {}

def show_investment(investment) -> float:
    '''
    prints the details of the investment and returns the total value
    '''
    if investment["Ticker"] != "":
        dat = yf.Ticker(investment["Ticker"])
        basic_info = dat.get_fast_info()        
        value = basic_info.last_price * investment["Quantity"]
        
        if investment["Currency"] == "USD":
            value = value* USDCAD
        valueUSD = value / USDCAD
        print(f'{investment["Name"]} {investment["Ticker"]}: Price: ${basic_info.last_price:,.2f} {investment["Currency"]}: Market Value=${value:,.2f} CAD (${valueUSD:,.2f} USD)')
    
    investment_list[investment["Ticker"]] = {value, investment["ExpenseRatio"]}

    return value, investment["Type"]

def get_currency_conversion(ticker) -> float:
    dat = yf.Ticker(ticker)
    print(dat)
    info = dat.get_fast_info()
    value = info.last_price
    print(f"Currency {ticker} = ${value:,.2f}")
    return value

USDCAD = get_currency_conversion(currency_ticker)

for investment in investments:
    value, type = show_investment(investment)
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
        print(f"Unknown investment type: {type}")
    tot_cad += value


print (f'\n\nCash = ${CASH_CAD:,.2f} CAD')
print (f'Cash = ${CASH_USD:,.2f} USD')

total_cash = CASH_CAD + (CASH_USD * USDCAD)
tot_cad += CASH_CAD
tot_cad += CASH_USD * USDCAD

if use_future:
    tot_cad += FUTURE
   
for ticker in investment_list:
    expense_ratio, value = investment_list[ticker]
    if ticker != "":
        investment_expense += value * expense_ratio /100
        expense_ratio_net += value * expense_ratio / tot_cad
        print(f'{ticker}: ${value:,.2f} : {expense_ratio:,.2f}%')

print(f'\n\nInvestment Expense = ${investment_expense:,.2f} CAD')
print(f'Net Expense Ratio = {expense_ratio_net:,.2f}%')        
print(f'\n\nTotal Investments = {tot_cad:,.2f} CAD\n\n')
print(f'Total Cash = {total_cash:,.2f} CAD : %Cash = {total_cash/tot_cad *100:,.2f}%')
print(f'Total International Stock = {total_intl_stock:,.2f} CAD : %Intl = {total_intl_stock/tot_cad *100:,.2f}%')
print(f'Total Canadian Stock = {total_canadian_stock:,.2f} CAD :  %Canada = {total_canadian_stock/tot_cad *100:,.2f}%')
print(f'Total US Stock = {total_domestic_stock:,.2f} CAD :  %US = {total_domestic_stock/tot_cad *100:,.2f}%')
print(f'Total Bond = {total_bond:,.2f} CAD : %Bond = {total_bond/tot_cad *100:,.2f}%')
twopointfivepercent_value = tot_cad * .025
threepercent_value = tot_cad *.03
threepointfivepercent_value =  tot_cad * .035
fourpercent_value = tot_cad * .04

onetwentyfivek = 125000 / tot_cad * 100 + expense_ratio_net
print(f'2.5% of Total = ${twopointfivepercent_value:,.2f} CAD')
print(f'3.0% of Total = ${threepercent_value:,.2f} CAD')
print(f'3.5% of Total = ${threepointfivepercent_value:,.2f} CAD')
print(f'4.0% of Total = ${fourpercent_value:,.2f} CAD')

print(f'125k with investment expenses = {onetwentyfivek:,.2f}')