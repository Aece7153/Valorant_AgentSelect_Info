import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set up folder path
DATA_DIR = '../../Downloads/Valorant_AgentSelect_Info-main (1)/Valorant_AgentSelect_Info-main/data'  # change if needed

# Read and combine all CSV files
def load_all_data(directory):
    data_frames = []
    for file in os.listdir(directory):
        if file.endswith('.csv'):
            path = os.path.join(directory, file)
            df = pd.read_csv(path, header=None)
            df.columns = ['Area', 'Agent', 'Role', 'Value1', 'Value2', 'Value3']
            data_frames.append(df)
    return pd.concat(data_frames, ignore_index=True)

# Load data
df = load_all_data(DATA_DIR)

# Strip whitespace
df['Agent'] = df['Agent'].str.strip().str.lower()
df['Role'] = df['Role'].str.strip().str.lower()

# --- BASIC ANALYTICS ---
print("\nTop 5 Most Frequent Agents:")
print(df['Agent'].value_counts().head())

print("\nTop 5 Roles by Frequency:")
print(df['Role'].value_counts().head())

# 1. Agent frequency
plt.figure(figsize=(10, 6))
sns.countplot(data=df, x='Agent', order=df['Agent'].value_counts().index)
plt.title('Agent Frequency')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('agent_frequency.png')

# 2. Role distribution
plt.figure(figsize=(6, 6))
df['Role'].value_counts().plot.pie(autopct='%1.1f%%', startangle=90)
plt.title('Role Distribution')
plt.ylabel('')
plt.tight_layout()
plt.savefig('role_distribution.png')



print("\nGraphs saved as PNG files in current directory.")
