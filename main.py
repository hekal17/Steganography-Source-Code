''' This is a steganography program GUI that hides secret messages within BMP image files 
using the Least Significant Bit (LSB) method. 
The program takes a message and unaltered image from the user, secretly embeds the message 
into the image, and returns it. 
It can also decode BMP images with secret messages hidden within. 
Made by Mostafa Hekal. '''

from encode import Encode
from decode import Decode

# Main Program

def main():
    """Main menu that lets the user choose what they want to do."""
    print("Welcome to the Steganography Station!")
    
    # Keep showing the menu until user chooses to exit
    while True:
        print("\nPlease choose an option:")
        print("1. Encode (hide a message in an image)")
        print("2. Decode (extract a hidden message from an image)")
        print("3. Exit")
        
        user_choice = input("Enter your choice (1, 2, or 3): ")
        
        if user_choice == '1':
            Encode()
        elif user_choice == '2':
            Decode()
        elif user_choice == '3':
            print("Goodbye! I hope you enjoyed your stay. <3")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


# Start the program
main()