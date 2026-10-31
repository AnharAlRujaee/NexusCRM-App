import shutil
import pandas as pd

# 1. Copy files so the originals remain untouched
shutil.copy('Applications.xlsx', 'Applications_copy.xlsx')

# 2. Test reading the data
try:
    df_apps = pd.read_excel('Applications_copy.xlsx', sheet_name='Applications')
    
    # 3. Identify relevant columns
    relevant_cols = ['Full Name', 'Email', 'Mentor Meeting']
    df_filtered = df_apps[relevant_cols]
    
    print("Data read successfully!")
    print(df_filtered.head())
    
except Exception as e:
    print(f"Error reading data: {e}")