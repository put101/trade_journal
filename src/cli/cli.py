import os
import argparse

def create_trade(trade_name):
    """
    Create a trade folder named trade_name in the current directory
    and add an empty Markdown file trade_name.md inside it.
    """
    cwd = os.getcwd()
    trade_folder = os.path.join(cwd, trade_name)
    
    # Create the folder (if it already exists, no error will be raised).
    os.makedirs(trade_folder, exist_ok=True)
    
    markdown_path = os.path.join(trade_folder, f"{trade_name}.md")
    
    # Create an empty Markdown file.
    with open(markdown_path, "w") as md_file:
        md_str= f"# {trade_name}\n\n"
        md_file.write(md_str)
        pass
    
    print(f"Created folder '{trade_folder}' with empty markdown file '{markdown_path}'.")

def main():
    parser = argparse.ArgumentParser(description="Create a trade folder with an empty Markdown file.")
    parser.add_argument("trade_name", help="The name of the trade folder to create")
    args = parser.parse_args()
    create_trade(args.trade_name)

if __name__ == "__main__":
    main()
