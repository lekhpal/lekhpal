import pandas as pd
import argparse
from datetime import datetime

def parse_arguments():
    parser = argparse.ArgumentParser(description='Calculate capital gains from stock transactions.')
    parser.add_argument('input_file', type=str, help='Input CSV file containing transactions.')
    parser.add_argument('output_file', type=str, help='Output CSV file for the results.')
    return parser.parse_args()

def load_transactions(input_file):
    transactions = pd.read_csv(input_file)
    transactions['Transaction Date'] = pd.to_datetime(transactions['Transaction Date'], format='%d-%b-%Y')
    transactions['Rate'] = transactions['Rate'].str.replace(',', '').astype(float)
    transactions['Amount'] = transactions['Amount'].str.replace(',', '').astype(float)
    return transactions

def calculate_capital_gains(transactions):
    results = []
    
    # Separate buy and sell transactions
    buys = transactions[transactions['Transaction Type'] == 'Buy']
    sells = transactions[transactions['Transaction Type'] == 'Sell']
    
    transactions = transactions.sort_values(by='Transaction Date')
    # FIFO matching
    for _, sell in sells.iterrows():
        scrip_name = sell['Scrip Name']
        sell_date = sell['Transaction Date']
        sell_quantity = sell['Quantity']
        sell_rate = sell['Rate']
        sell_amount = sell['Amount']
        sell_expense = sell['Expenses']
        
        # Filter buys for the same scrip
        relevant_buys = buys[buys['Scrip Name'] == scrip_name]
        
        #print("sell transaction - [%s][%s][%d][%.2f][%.2f][%.2f]" % (scrip_name, str(sell_date), sell_quantity, sell_rate, sell_amount, sell_expense))
        for _, buy in relevant_buys.iterrows():
            if sell_quantity <= 0:
                break
            
            buy_quantity = buy['Quantity']

            matched_quantity = min(buy_quantity, sell_quantity)

            buy_rate = buy['Rate']
            buy_amount = buy['Amount'] * matched_quantity / buy_quantity
            buy_expense = buy['Expenses'] * matched_quantity / buy_quantity
            transaction_sell_amount = sell_amount * matched_quantity / sell['Quantity']
            transaction_sell_expense = sell_expense * matched_quantity / sell['Quantity']
            holding_period_months = (sell_date - buy['Transaction Date']).days // 30
            
            gain = (transaction_sell_amount - buy_amount - transaction_sell_expense - buy_expense)
            
            short_term_gain = gain if holding_period_months < 12 else 0
            long_term_gain = gain if holding_period_months >= 12 else 0
            
            results.append({
                'Scrip Name': scrip_name,
                'Date of Purchase': buy['Transaction Date'],
                'Quantity': matched_quantity,
                'Purchase Rate': buy_rate,
                'Purchase Amount': buy_amount,
                'Purchase Expense': buy_expense,
                'Holding Period (Months)': holding_period_months,
                'Date of Sale': sell_date,
                'Sell Rate': sell_rate,
                'Sell Amount': transaction_sell_amount,
                'Sell Expense': transaction_sell_expense,
                'Short Term Capital Gain': short_term_gain,
                'Long Term Capital Gain': long_term_gain
            })
            
            # Update quantities
            sell_quantity -= matched_quantity
            if matched_quantity < buy_quantity:
                # Update the remaining quantity of the buy transaction
                buys.loc[buy.name, 'Quantity'] -= matched_quantity
                buys.loc[buy.name, 'Amount'] -= buy_amount
                buys.loc[buy.name, 'Expenses'] -= buy_expense
            if matched_quantity == buy_quantity:
                buys = buys.drop(buy.name)
    
    return pd.DataFrame(results)

def save_results(results, output_file):
    results.to_csv(output_file, index=False)

def main():
    args = parse_arguments()
    
    transactions = load_transactions(args.input_file)
    
    results = calculate_capital_gains(transactions)
    
    save_results(results, args.output_file)
    
if __name__ == '__main__':
    main()
