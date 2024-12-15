import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import requests
import sys

# Fetch the AIPROXY_TOKEN from environment variables
AIPROXY_TOKEN = os.environ.get("AIPROXY_TOKEN")
if not AIPROXY_TOKEN:
    print("Error: AIPROXY_TOKEN environment variable is not set.")
    sys.exit(1)

# AI Proxy API URL
AIPROXY_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

def fetch_llm_response(prompt, max_tokens=500):
    """
    Fetch response from LLM with the given prompt using the AI Proxy API.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}",
    }

    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(AIPROXY_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        print("LLM Response:", result)  # Print the raw response from LLM for debugging
        return result['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with LLM: {e}")
        return None

def analyze_data(file_path):
    """
    Analyze the dataset, generate insights, visualizations, and a narrative.
    """
    # Attempt to read the CSV with 'utf-8' encoding first
    try:
        df = pd.read_csv(file_path)
        print(f"Loaded dataset: {file_path} using UTF-8 encoding.")
    except UnicodeDecodeError as e:
        print(f"UTF-8 decoding failed: {e}. Retrying with 'latin1' encoding...")
        try:
            df = pd.read_csv(file_path, encoding='latin1')
            print(f"Loaded dataset: {file_path} using 'latin1' encoding.")
        except Exception as e:
            print(f"Error reading file: {e}")
            return

    # Data summary
    summary = {
        "shape": df.shape,
        "columns": df.dtypes.to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "sample_data": df.head().to_dict(orient='records'),
    }

    # Generate correlation matrix if numeric columns exist
    numeric_columns = df.select_dtypes(include=np.number).columns
    if len(numeric_columns) > 1:
        corr_matrix = df[numeric_columns].corr()
        plt.figure(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f")
        plt.title("Correlation Matrix")
        corr_file = "correlation_matrix.png"
        plt.savefig(corr_file)
        plt.close()
    else:
        corr_file = None

    # Missing data visualization
    if df.isnull().sum().sum() > 0:
        plt.figure(figsize=(12, 6))
        sns.heatmap(df.isnull(), cbar=False, cmap="viridis")
        plt.title("Missing Data Heatmap")
        missing_file = "missing_data.png"
        plt.savefig(missing_file)
        plt.close()
    else:
        missing_file = None

    # Histogram of the first numeric column
    if len(numeric_columns) > 0:
        example_col = numeric_columns[0]
        plt.figure(figsize=(8, 6))
        sns.histplot(df[example_col].dropna(), kde=True, bins=30, color="blue")
        plt.title(f"Distribution of {example_col}")
        hist_file = "histogram.png"
        plt.savefig(hist_file)
        plt.close()
    else:
        hist_file = None

    # Prepare data description for LLM
    prompt = (
        f"The dataset contains {df.shape[0]} rows and {df.shape[1]} columns.\n"
        f"The columns are:\n{df.dtypes.to_string()}\n"
        f"There are {df.isnull().sum().sum()} missing values in the dataset.\n"
        "Please analyze this data, suggest insights, and narrate a story."
    )

    # Fetch analysis from LLM
    narrative = fetch_llm_response(prompt, max_tokens=1000)

    # Write results to README.md
    with open("README.md", "w") as readme:
        readme.write("# Automated Data Analysis\n")
        readme.write(f"## Dataset Summary\n- Shape: {df.shape}\n")
        readme.write("### Column Information:\n")
        readme.write(f"{df.dtypes.to_string()}\n\n")
        readme.write("### Missing Data:\n")
        readme.write(f"{df.isnull().sum().to_string()}\n\n")
        if narrative:
            readme.write(f"## Narrative Analysis\n{narrative}\n\n")
        readme.write("## Visualizations\n")
        if corr_file:
            readme.write(f"![Correlation Matrix]({corr_file})\n")
        if missing_file:
            readme.write(f"![Missing Data Heatmap]({missing_file})\n")
        if hist_file:
            readme.write(f"![Histogram of {example_col}]({hist_file})\n")

    print("Analysis complete. Outputs generated: README.md and visualization PNGs.")
    print(f"Files generated: README.md, {corr_file if corr_file else ''}, {missing_file if missing_file else ''}, {hist_file if hist_file else ''}")

if __name__ == "__main__":
    # Accept CSV filename as an argument (from command line or uv)
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py <dataset.csv>")
        sys.exit(1)

    file_path = sys.argv[1]

    # Analyze the dataset
    analyze_data(file_path)
