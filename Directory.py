import os

def list_directory_structure(root_dir, indent_level=0, max_depth=float('inf'), current_depth=0):
    if current_depth > max_depth:
        # Print a placeholder if max depth is exceeded
        print(' ' * indent_level + '|-- ...')
        return

    # Get list of items in the directory
    items = os.listdir(root_dir)
    
    # Sort items to make the output consistent
    items.sort()
    
    for item in items:
        # Create full path to item
        full_path = os.path.join(root_dir, item)
        
        # Print item with indentation
        print(' ' * indent_level + '|-- ' + item)
        
        # If item is a directory, recursively list its contents
        if os.path.isdir(full_path):
            list_directory_structure(full_path, indent_level + 4, max_depth, current_depth + 1)

def main():
    # Get the current working directory
    current_directory = os.getcwd()
    
    # Ask user how many layers deep they want to go
    user_input = input("Enter the number of layers deep to display (0 for unlimited): ").strip()
    
    # Set max_depth based on user input
    if user_input == '0':
        max_depth = float('inf')  # Unlimited layers
    else:
        try:
            max_depth = int(user_input)
            if max_depth < 0:
                print("Please enter a non-negative number.")
                return
        except ValueError:
            print("Invalid input. Please enter a valid number.")
            return
    
    print(f"\nDirectory structure of: {current_directory}\n")
    
    # Print the current working directory
    print(f"{current_directory}")
    
    # List the directory structure starting from the current directory
    list_directory_structure(current_directory, max_depth=max_depth)

if __name__ == "__main__":
    main()
