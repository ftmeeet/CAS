import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import ast

def plot_time_predictions(predictions_file='data/predictions_with_time.csv'):
    """
    Plot time-based predictions showing probability and distance trends.
    
    Args:
        predictions_file (str): Path to the predictions CSV file
    """
    try:
        # Read predictions
        df = pd.read_csv(predictions_file)
        
        # Convert string lists to actual lists
        df['All_Times'] = df['All_Times'].apply(ast.literal_eval)
        df['All_Probabilities'] = df['All_Probabilities'].apply(ast.literal_eval)
        df['All_Distances'] = df['All_Distances'].apply(ast.literal_eval)
        
        # Get top 5 pairs
        top_5 = df.nlargest(5, 'Max_Probability')
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        
        # Plot 1: Probability over time
        for idx, row in top_5.iterrows():
            times = [datetime.strptime(t, '%Y-%m-%d %H:%M:%S') for t in row['All_Times']]
            ax1.plot(times, row['All_Probabilities'], 
                    label=f"{row['Satellite1']} - {row['Satellite2']}",
                    marker='o')
        
        ax1.set_title('Conjunction Probability Over Time (Top 5 Pairs)')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Probability')
        ax1.grid(True)
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Plot 2: Distance over time
        for idx, row in top_5.iterrows():
            times = [datetime.strptime(t, '%Y-%m-%d %H:%M:%S') for t in row['All_Times']]
            ax2.plot(times, row['All_Distances'], 
                    label=f"{row['Satellite1']} - {row['Satellite2']}",
                    marker='o')
        
        ax2.set_title('Minimum Distance Over Time (Top 5 Pairs)')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Distance (km)')
        ax2.grid(True)
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        # Adjust layout and save
        plt.tight_layout()
        plt.savefig('data/time_predictions_plot.png', bbox_inches='tight')
        print("Plot saved to data/time_predictions_plot.png")
        
        # Print summary for top pairs
        print("\nSummary of Top 5 Pairs:")
        for idx, row in top_5.iterrows():
            print(f"\n{row['Satellite1']} - {row['Satellite2']}")
            print(f"Maximum Probability: {row['Max_Probability']:.3f}")
            print(f"Time of Maximum Probability: {row['Time_of_Max_Probability']}")
            print(f"Distance at Maximum Probability: {row['Distance_at_Max_Probability']:.2f} km")
            print(f"Probability Range: {min(row['All_Probabilities']):.3f} - {max(row['All_Probabilities']):.3f}")
            print(f"Distance Range: {min(row['All_Distances']):.2f} - {max(row['All_Distances']):.2f} km")
        
    except Exception as e:
        print(f"Error plotting predictions: {e}")

if __name__ == "__main__":
    plot_time_predictions() 