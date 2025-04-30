import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def plot_predictions(predictions_file='data/predictions.csv'):
    """
    Plot predictions from the CSV file.
    
    Args:
        predictions_file (str): Path to the predictions CSV file
    """
    try:
        # Read predictions
        df = pd.read_csv(predictions_file)
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot 1: Probability Distribution
        sns.histplot(data=df, x='Probability', bins=20, ax=ax1)
        ax1.set_title('Distribution of Conjunction Probabilities')
        ax1.set_xlabel('Probability')
        ax1.set_ylabel('Number of Pairs')
        
        # Add mean and median lines
        mean_prob = df['Probability'].mean()
        median_prob = df['Probability'].median()
        ax1.axvline(mean_prob, color='r', linestyle='--', label=f'Mean: {mean_prob:.3f}')
        ax1.axvline(median_prob, color='g', linestyle='--', label=f'Median: {median_prob:.3f}')
        ax1.legend()
        
        # Plot 2: Top 10 Most Likely Conjunctions
        top_10 = df.nlargest(10, 'Probability')
        sns.barplot(data=top_10, x='Probability', y='Satellite1', ax=ax2)
        ax2.set_title('Top 10 Most Likely Conjunctions')
        ax2.set_xlabel('Probability')
        ax2.set_ylabel('Satellite Pair')
        
        # Add probability values on the bars
        for i, v in enumerate(top_10['Probability']):
            ax2.text(v, i, f'{v:.3f}', va='center')
        
        # Adjust layout and save
        plt.tight_layout()
        plt.savefig('data/predictions_plot.png')
        print("Plot saved to data/predictions_plot.png")
        
        # Show summary statistics
        print("\nSummary Statistics:")
        print(f"Total pairs analyzed: {len(df)}")
        print(f"Mean probability: {mean_prob:.3f}")
        print(f"Median probability: {median_prob:.3f}")
        print(f"Maximum probability: {df['Probability'].max():.3f}")
        print(f"Minimum probability: {df['Probability'].min():.3f}")
        
    except Exception as e:
        print(f"Error plotting predictions: {e}")

if __name__ == "__main__":
    plot_predictions() 