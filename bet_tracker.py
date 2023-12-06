import csv
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def record_bet():
    bet = {}

    bet['name'] = input("Enter the name of the bet: ")
    bet['amount'] = float(input("Enter the amount of the bet: "))
    bet['odds'] = float(input("Enter the odds for the bet: "))
    
    
    
        
    
    # Calculate implied percentage
    bet['implied_percentage'] = 1 / bet['odds']
    
    bet['historical_percentage'] = float(input("Enter the historical percentage for the bet: "))
    
    result_input = input("Enter the result of the bet (win/loss): ").lower()
    bet['result'] = 1 if result_input == 'win' else 0  # 1 for win, 0 for loss

    # Additional inputs
    bet['market'] = input("Enter the market for the bet: ")
    bet['prop'] = input("Enter the prop for the bet: ")
    

    return bet

def calculate_difference(bet):
    implied_percentage = bet['implied_percentage']
    historical_percentage = bet['historical_percentage']
    difference = round(abs(implied_percentage - historical_percentage), 2)
    return difference

def save_to_csv(bets):
    with open('tracking/bet_tracker.csv', 'w', newline='') as csvfile:
        fieldnames = ['name','market','prop','amount', 'odds', 'implied_percentage', 'historical_percentage', 'difference', 'result', 'timestamp','running_total']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for bet in bets:
            writer.writerow(bet)

def update_results(bets):
    current_time = datetime.now()

    print("\n=== Update Results ===")
    for index, bet in enumerate(bets, start=1):
        bet_time = datetime.strptime(bet['timestamp'], '%Y-%m-%d')
        time_difference = current_time - bet_time

        if time_difference < timedelta(days=1):
            print(f"\nBet {index} - {bet['name']}:")
            result_input = input("Enter the result of the bet (win/loss): ").lower()
            bet['result'] = 1 if result_input == 'win' else 0  # 1 for win, 0 for loss
            bet['timestamp'] = current_time.strftime('%Y-%m-%d')

    save_to_csv(bets)
    print("Results updated and saved to CSV file (bet_tracker.csv).")

def delete_bet(bets):
    if not bets:
        print("No bets recorded yet.")
        return

    print("\n=== Delete Bet ===")
    for index, bet in enumerate(bets, start=1):
        print(f"{index}. Bet {index} - {bet['name']}")

    try:
        bet_index = int(input("Enter the index of the bet you want to delete: "))
        if 1 <= bet_index <= len(bets):
            deleted_bet = bets.pop(bet_index - 1)
            print(f"Bet {bet_index} - {deleted_bet['name']} deleted successfully.")
        else:
            print("Invalid index. No bet deleted.")
    except ValueError:
        print("Invalid input. Please enter a valid index.")

    save_to_csv(bets)
    
def calculate_running_total(bets):
    running_total = 0

    for bet in bets:
        if bet['result'] == 1:  # 1 for win
            running_total += (float(bet['amount']) * float(bet['odds'])) - float(bet["amount"])
        else:
            running_total -= float(bet['amount'])

        bet['running_total'] = running_total

    return bets

def plot_trend(bets):
    # Line graph for the running total
    running_totals = [bet['running_total'] for bet in bets]
    
    # Plot the line graph
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)  # 1 row, 2 columns, first subplot
    plt.plot(running_totals, marker='o', linestyle='-', color='b')
    plt.title('Running Total Trend')
    plt.xlabel('Bet Number')
    plt.ylabel('Running Total')

    # Histogram for different odds ranges
    odds = [float(bet['odds']) for bet in bets if 'odds' in bet]


    # Plot the histogram
    plt.subplot(1, 2, 2)  # 1 row, 2 columns, second subplot
    # Use a large value instead of np.inf
    bins = [1,1.49,1.99,2.49,2.99,3.49,3.99,4.49,4.99,5.49,5.99,6.49,6.99,7.49,7.99,8.49,8.99,9.49,9.99,10.49,10.99]
    plt.hist(odds, bins=bins, edgecolor='black', color='green', alpha=0.7)

    plt.title('Histogram for Odd Frequency')
    plt.xlabel('Odds')
    plt.ylabel('Frequency')

    # Adjust layout to prevent clipping of titles
    plt.tight_layout()

    # Show the plots
    plt.show()


    
def update_running_total(bets):
    running_total = 0

    for bet in bets:
        if bet['result'] == '1':  # '1' for win
            running_total += float(bet['amount']) * float(bet['odds'])
        else:
            running_total -= float(bet['amount'])

        bet['running_total'] = running_total

    return bets

def main():
    bets = []
    hit_rates = []  # List to store hit rates for trend analysis
    std_devs = []   # List to store standard deviations for trend analysis

    # Load existing bets from CSV file
    try:
        with open('tracking/bet_tracker.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                bets.append(row)
    except FileNotFoundError:
        print("No existing CSV file found. Starting with an empty list of bets.")

    while True:
        print("\n=== Bet Tracker ===")
        print("1. Record a new bet")
        print("2. View all bets")
        print("3. Update results for bets placed in the last 24 hours")
        print("4. Delete a bet")
        print("5. Save to CSV")
        print("6. Exit")

        choice = input("Enter your choice (1/2/3/4/5/6): ")

        if choice == '1':
            new_bet = record_bet()
            new_bet['timestamp'] = datetime.now().strftime('%Y-%m-%d')
            difference = calculate_difference(new_bet)
            new_bet['difference'] = difference
            bets.append(new_bet)
            print("Bet recorded successfully!")

            # Update trend analysis data
            hit_rate = sum(int(bet['result']) for bet in bets) / len(bets)
            hit_rates.append(hit_rate)
            std_dev = calculate_std_dev(bets)
            std_devs.append(std_dev)
            calculate_running_total(bets)

        elif choice == '2':
            if not bets:
                print("No bets recorded yet.")
            else:
                print("\n=== All Bets ===")
                for index, bet in enumerate(bets, start=1):
                    print(f"\nBet {index}:")
                    for key, value in bet.items():
                        print(f"{key.capitalize()}: {value}")

        elif choice == '3':
            if not bets:
                print("No bets recorded yet.")
            else:
                update_results(bets)
                calculate_running_total(bets)

                # Update trend analysis data after results are updated
                hit_rate = sum(int(bet['result']) for bet in bets) / len(bets)
                hit_rates.append(hit_rate)
                std_dev = calculate_std_dev(bets)
                std_devs.append(std_dev)

        elif choice == '4':
            delete_bet(bets)
            try:
                # Update trend analysis data after a bet is deleted
                hit_rate = sum(int(bet['result']) for bet in bets) / len(bets)
                hit_rates.append(hit_rate)
                std_dev = calculate_std_dev(bets)
                std_devs.append(std_dev)
            except ZeroDivisionError:
                pass

        elif choice == '5':
            save_to_csv(bets)
            print("Bets saved to CSV file (bet_tracker.csv).")

        elif choice == '6':
            bets = update_running_total(bets)
            # Plot trend analysis before exiting
            plot_trend(bets)
            print("Exiting the Bet Tracker.")
            break

        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, 5, or 6.")



def calculate_std_dev(bets):
    # Calculate the standard deviation of the results
    results = [int(bet['result']) for bet in bets]
    return round((sum((result - sum(results) / len(results)) ** 2 for result in results) / len(results)) ** 0.5, 2)

if __name__ == "__main__":
    main()