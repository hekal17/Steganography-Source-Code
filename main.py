''' This is a steganography program GUI that hides secret messages within BMP image files 
using the Least Significant Bit (LSB) method. 
The program takes a message and unaltered image from the user, secretly embeds the message 
into the image, and returns it. 
It can also decode BMP images with secret messages hidden within. 
Made by Mostafa Hekal. '''

# Main Program

def main():
    print("Welcome to the Steganography Station!")
    while True:
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
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def Encode():
    secret_text = input("Please enter the secret message: ")
    image_file_path = input("Please enter the path to the BMP image file: ")
    
    # File existence check
    try:
        with open(image_file_path, 'rb') as img_file:
            img_bytes = bytearray(img_file.read())
    except FileNotFoundError:
        print("Error: Image file was not found.")
        return
    
    if img_bytes[:2] != b'BM':
        print("Sorry, only BMP image files are supported.")
        return
    
    if not secret_text:
        print("Error: Secret message cannot be empty.")
        return
    
    # Convert secret text to binary
    binary_message = ''.join(format(ord(char), '08b') for char in secret_text) # Convert each character to 8-bit binary
    delimiter = '1111111111111110'  # 16-bit delimiter
    full_data = binary_message + delimiter
    
    # Check BMP header size
    if len(img_bytes) < 54:
        print(" Error: BMP file header is too small or corrupted.") 
        return
    
    # Read pixel data offset from BMP header
    pixel_data_offset = int.from_bytes(img_bytes[10:14], byteorder='little')
    
    if pixel_data_offset > len(img_bytes):
        print(" Error: Pixel data offset is beyond the file size.") 
        return
    
    # Read bits per pixel from BMP header
    bits_per_pixel = int.from_bytes(img_bytes[28:30], byteorder='little')
    
    # 24 bit RGB image
    if bits_per_pixel == 24:
        available_bits = len(img_bytes) - 54  # Each byte can hold 1 bit in LSB
        if len(full_data) > available_bits:  # 54 bytes is the BMP header size
            print("Error: The message is too long for this image.")
            return
        
        for i in range(len(full_data)):
            img_bytes[i + 54] = (img_bytes[i + 54] & 0b11111110) | int(full_data[i])
        
    # 32 bit RGBA image
    elif bits_per_pixel == 32:
        available_bits = (len(img_bytes) - 54) // 4 * 3 # Each pixel has 4 bytes, we can use 3 bytes for data
        if len(full_data) > available_bits:
            print("Error: The message is too long for this image.")
            return
        
        data_index = 0
        for i in range(54, len(img_bytes), 4):
            for j in range(3):  # Use only R, G, B channels
                if data_index < len(full_data):
                    img_bytes[i + j] = (img_bytes[i + j] & 0b11111110) | int(full_data[data_index])
                    data_index += 1
                else:
                    break
                
    # 8-bit greyscale image
    elif bits_per_pixel == 8:
        print("Error: Encoding into 8-bit BMP images is not supported due to palette handling complexity.")
        return
    else:
        print("Error: Unsupported BMP format.")
        return
        
    # Save the new image
    new_image_path = input("Please enter the filename for the new image with .bmp extension (e.g., secret.bmp): ")
    if not new_image_path.lower().endswith('.bmp'):
        new_image_path += '.bmp'
    with open(new_image_path, 'wb') as new_img_file:
        new_img_file.write(img_bytes)
        
    print(f"Success! Your secret message has been encoded into {new_image_path}.")








main()