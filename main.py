''' This is a steganography program GUI that hides secret messages within image files 
using the Least Significant Bit (LSB) method. 
The program takes a message and unaltered image from the user, secretly embeds the message 
into the image, and returns it. 
It can also decode images with secret messages hidden within. 
Made by Mostafa Hekal. '''

# Main Program

def main():
    print("Welcome to the Steganography Station!")
    print("Please choose an option:")
    print("1. Encode")
    print("2. Decode")
    print("3. Exit")
    
    user_choice = input("Enter your choice (1, 2, or 3): ")
    
    if user_choice == '1':
        Encode()
    elif user_choice == '2':
        Decode()
    elif user_choice == '3':
        print("Goodbye! We hope you enjoyed your stay. <3")
    else:
        print("Invalid choice. Please enter 1, 2, or 3.")
        
main()