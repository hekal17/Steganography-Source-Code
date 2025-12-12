''' This is a steganography program GUI that hides secret messages within BMP image files 
using the Least Significant Bit (LSB) method. 
The program takes a message and unaltered image from the user, secretly embeds the message 
into the image, and returns it. 
It can also decode BMP images with secret messages hidden within. 
Made by Mostafa Hekal. '''

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
            






def Encode():
# This function hides a secret message inside a BMP image file.
    
    # Step 1: Get the secret message from the user
    print("\nHow would you like to provide the secret message?")
    print("1. Type the message directly")
    print("2. Provide a path to a text file")
    
    message_choice = input("Enter your choice (1 or 2): ").strip()
    secret_text = ""
    
    if message_choice == '1':
        secret_text = input("Please enter the secret message: ")
        
    elif message_choice == '2':
        text_file_path = input("Please enter the path to the text file: ").strip()
        try:
            # Try to open and read the file
            text_file = open(text_file_path, 'r', encoding='utf-8')
            secret_text = text_file.read()
            text_file.close()
        except FileNotFoundError:
            print("Error: Text file was not found.")
            return
        except Exception as e:
            print(f"Error: Could not read the text file. {str(e)}")
            return
    else:
        print("Invalid choice. Please enter 1 or 2.")
        return
    
    # Make sure the message isn't empty
    if not secret_text:
        print("Error: Secret message cannot be empty.")
        return
    
    # Step 2: Get the image file from the user
    image_file_path = input("Please enter the path to the BMP image file: ")
    
# File existence check
    try:
        img_file = open(image_file_path, 'rb')  # 'rb' means read in binary mode
        img_bytes = bytearray(img_file.read())   # Read all bytes and convert to bytearray so we can modify it
        img_file.close()
    except FileNotFoundError:
        print("Error: Image file was not found.")
        return
    
    # Step 4: Check if it's actually a BMP file
    # BMP files always start with 'BM' (that's how you identify them)
    if img_bytes[0:2] != b'BM':
        print("Sorry, only BMP image files are supported.")
        return
    
    # Step 5: Check if the file is big enough to have a valid header
    # BMP headers are at least 54 bytes long
    if len(img_bytes) < 54:
        print("Error: BMP file header is too small or corrupted.")
        return
    
    # Step 6: Convert the secret message to binary
    # Each character becomes 8 bits (1 byte) of binary data
    binary_message = ""
    for char in secret_text:
        # ord() gets the ASCII/Unicode number for the character
        # format(..., '08b') converts it to 8-bit binary (with leading zeros)
        char_binary = format(ord(char), '08b')
        binary_message = binary_message + char_binary
    
    # Step 7: Add a delimiter to mark where the message ends
    # This is a special pattern: 0000000000000001 (16 zeros then a 1)
    # When we decode, we'll look for this pattern to know when to stop reading
    delimiter = '0000000000000001'
    full_data = binary_message + delimiter
    
    # Step 8: Read information from the BMP header
    # The header tells us where the pixel data starts and what format the image is
    
    # Find where the pixel data starts (bytes 10-13 in the header)
    pixel_data_offset = int.from_bytes(img_bytes[10:14], byteorder='little')
    
    # Make sure the offset makes sense
    if pixel_data_offset < 54:
        print("Error: Invalid pixel data offset in BMP header.")
        return
    if pixel_data_offset > len(img_bytes):
        print("Error: Pixel data offset is beyond the file size.")
        return
    
    # Check if the image is compressed (we only support uncompressed images)
    # Bytes 30-33 tell us the compression type (0 means no compression)
    compression = int.from_bytes(img_bytes[30:34], byteorder='little')
    if compression != 0:
        print("Error: Only uncompressed BMP files are supported.")
        return
    
    # Find out how many bits per pixel (bytes 28-29)
    # This tells us if it's 24-bit (3 bytes per pixel) or 32-bit (4 bytes per pixel)
    bits_per_pixel = int.from_bytes(img_bytes[28:30], byteorder='little')
    
    # Step 9: Hide the message in the image
    # We handle 24-bit and 32-bit images differently
    
    if bits_per_pixel == 24:
        # 24-bit images: Each pixel has 3 bytes (Blue, Green, Red)
        # Note: BMP stores colors as BGR, not RGB!
        
        # Get the image width and height (bytes 18-21 for width, 22-25 for height)
        width = int.from_bytes(img_bytes[18:22], byteorder='little')
        height = int.from_bytes(img_bytes[22:26], byteorder='little', signed=True)
        # Height can be negative (means image is stored top-to-bottom instead of bottom-to-top)
        
        # Validate the dimensions
        if width <= 0:
            print("Error: Invalid image width.")
            return
        if height == 0:
            print("Error: Invalid image height.")
            return
        
        # Calculate how much space we have
        # BMP rows must be a multiple of 4 bytes, so there might be padding
        bytes_per_pixel = 3  # 24-bit = 3 bytes per pixel
        bytes_per_row_without_padding = width * bytes_per_pixel
        # Round up to nearest multiple of 4
        bytes_per_row = ((bytes_per_row_without_padding + 3) // 4) * 4
        
        # Total number of bytes in all rows
        number_of_rows = abs(height)  # Use absolute value since height might be negative
        total_pixel_bytes = bytes_per_row * number_of_rows
        
        # Also check how many bytes are actually in the file
        actual_available_bytes = len(img_bytes) - pixel_data_offset
        
        # Use whichever is smaller (to be safe)
        available_bits = min(total_pixel_bytes, actual_available_bytes)
        
        # Check if our message fits
        if len(full_data) > available_bits:
            print("Error: The message is too long for this image.")
            return
        
        # Now hide each bit of our message in the image
        # We go through each bit and change the last bit of each byte
        for bit_position in range(len(full_data)):
            # Calculate which byte in the image we're modifying
            byte_index = pixel_data_offset + bit_position
            
            # Get the current byte value
            current_byte = img_bytes[byte_index]
            
            # Clear the last bit (set it to 0) using bitwise AND with 11111110
            cleared_byte = current_byte & 0b11111110
            
            # Set the last bit to our message bit using bitwise OR
            message_bit = int(full_data[bit_position])  # Convert '0' or '1' to integer
            new_byte = cleared_byte | message_bit
            
            # Update the byte in the image
            img_bytes[byte_index] = new_byte
    
    elif bits_per_pixel == 32:
        # 32-bit images: Each pixel has 4 bytes (Blue, Green, Red, Alpha)
        # We'll use the first 3 bytes (B, G, R) and skip the Alpha channel
        
        # Get the image dimensions
        width = int.from_bytes(img_bytes[18:22], byteorder='little')
        height = int.from_bytes(img_bytes[22:26], byteorder='little', signed=True)
        
        # Validate dimensions
        if width <= 0:
            print("Error: Invalid image width.")
            return
        if height == 0:
            print("Error: Invalid image height.")
            return
        
        # Calculate available space
        # Each pixel has 4 bytes, we use 3 of them (skip Alpha)
        number_of_rows = abs(height)
        total_pixels = number_of_rows * width
        available_bits = total_pixels * 3  # 3 bytes per pixel we can use
        
        # Also check actual file size
        actual_available_bytes = len(img_bytes) - pixel_data_offset
        available_bits_from_file = (actual_available_bytes // 4) * 3
        
        # Use the smaller value
        available_bits = min(available_bits, available_bits_from_file)
        
        # Check if message fits
        if len(full_data) > available_bits:
            print("Error: The message is too long for this image.")
            return
        
        # Hide the message
        # We go through each pixel (every 4 bytes) and use the first 3 bytes
        data_index = 0  # Track which bit of our message we're on
        for pixel_start in range(pixel_data_offset, len(img_bytes), 4):
            # For each pixel, use the first 3 bytes (B, G, R)
            for channel in range(3):  # 0=Blue, 1=Green, 2=Red
                if data_index < len(full_data):
                    byte_index = pixel_start + channel
                    current_byte = img_bytes[byte_index]
                    cleared_byte = current_byte & 0b11111110
                    message_bit = int(full_data[data_index])
                    new_byte = cleared_byte | message_bit
                    img_bytes[byte_index] = new_byte
                    data_index = data_index + 1
                else:
                    break  # We've hidden all our data
            if data_index >= len(full_data):
                break  # Stop if we're done
    
    elif bits_per_pixel == 8:
        print("Error: Encoding into 8-bit BMP images is not supported.")
        return
    else:
        print("Error: Unsupported BMP format.")
        return
    
    # Step 10: Save the modified image
    new_image_path = input("Please enter the filename for the new image with .bmp extension (e.g., secret.bmp): ")
    
    # Make sure it ends with .bmp
    if not new_image_path.lower().endswith('.bmp'):
        new_image_path = new_image_path + '.bmp'
    
    # Write the file
    try:
        new_img_file = open(new_image_path, 'wb')  # 'wb' means write in binary mode
        new_img_file.write(img_bytes)
        new_img_file.close()
        print(f"Success! Your secret message has been encoded into {new_image_path}.")
    except Exception as e:
        print(f"Error: Could not save the image file. {str(e)}")
        return






def Decode():
    """This function extracts a hidden message from a BMP image file."""
    
    # Step 1: Get the image file from the user
    image_file_path = input("Please enter the path to the BMP image file with hidden message: ")
    
    # Step 2: Read the image file
    try:
        img_file = open(image_file_path, 'rb')
        img_bytes = bytearray(img_file.read())
        img_file.close()
    except FileNotFoundError:
        print("Error: Image file was not found.")
        return
    
    # Step 3: Check if it's a BMP file
    if img_bytes[0:2] != b'BM':
        print("Sorry, only BMP image files are supported.")
        return
    
    # Step 4: Check header size
    if len(img_bytes) < 54:
        print("Error: BMP file header is too small or corrupted.")
        return
    
    # Step 5: Read BMP header information
    pixel_data_offset = int.from_bytes(img_bytes[10:14], byteorder='little')
    
    if pixel_data_offset < 54:
        print("Error: Invalid pixel data offset in BMP header.")
        return
    if pixel_data_offset > len(img_bytes):
        print("Error: Pixel data offset is beyond the file size.")
        return
    
    # Check compression
    compression = int.from_bytes(img_bytes[30:34], byteorder='little')
    if compression != 0:
        print("Error: Only uncompressed BMP files are supported.")
        return
    
    # Get bits per pixel
    bits_per_pixel = int.from_bytes(img_bytes[28:30], byteorder='little')
    
    # Step 6: Extract the hidden bits
    # We'll look for our delimiter pattern to know when to stop
    delimiter = '0000000000000001'
    extracted_bits = ""  # This will hold all the bits we extract
    
    
    
    if bits_per_pixel == 24:
        # For 24-bit images, read bits from every byte starting at pixel data
        for byte_index in range(pixel_data_offset, len(img_bytes)):
            # Get the last bit of this byte using bitwise AND with 00000001
            last_bit = img_bytes[byte_index] & 0b00000001
            extracted_bits = extracted_bits + str(last_bit)
            
            # Check if we've found the delimiter (the end of the message)
            if len(extracted_bits) >= len(delimiter):
                # Check the last 16 bits to see if they match our delimiter
                last_16_bits = extracted_bits[-len(delimiter):]
                if last_16_bits == delimiter:
                    break  # Found the end!
    
    
    
    elif bits_per_pixel == 32:
        # For 32-bit images, read from first 3 bytes of each pixel
        for pixel_start in range(pixel_data_offset, len(img_bytes), 4):
            for channel in range(3):  # Use B, G, R (skip Alpha)
                byte_index = pixel_start + channel
                last_bit = img_bytes[byte_index] & 0b00000001
                extracted_bits = extracted_bits + str(last_bit)
                
                # Check for delimiter
                if len(extracted_bits) >= len(delimiter):
                    last_16_bits = extracted_bits[-len(delimiter):]
                    if last_16_bits == delimiter:
                        break  # Found it!
            # If we found the delimiter, break out of the outer loop too
            if len(extracted_bits) >= len(delimiter):
                last_16_bits = extracted_bits[-len(delimiter):]
                if last_16_bits == delimiter:
                    break
    
    
    
    elif bits_per_pixel == 8:
        print("Error: Decoding from 8-bit BMP images is not supported.")
        return
    else:
        print("Error: Unsupported BMP format.")
        return
    
    # Step 7: Check if we found a valid message
    if len(extracted_bits) < len(delimiter):
        print("Error: No valid hidden message found in this image.")
        return
    
    # Check if the last bits match our delimiter
    last_16_bits = extracted_bits[-len(delimiter):]
    if last_16_bits != delimiter:
        print("Error: No valid hidden message found in this image.")
        return
    
    # Step 8: Remove the delimiter to get just the message bits
    message_bits = extracted_bits[:-len(delimiter)]
    
    # Step 9: Convert binary back to text
    # Each 8 bits represents one character
    message = ""
    for i in range(0, len(message_bits), 8):
        # Get the next 8 bits
        byte_bits = message_bits[i:i+8]
        
        if len(byte_bits) == 8:
            try:
                # Convert binary string to a number
                char_code = int(byte_bits, 2)
                
                # Make sure it's a valid character code
                if 0 <= char_code <= 1114111:  # Valid Unicode range
                    # Convert number to character
                    char = chr(char_code)
                    message = message + char
                else:
                    break  # Invalid character code, stop
            except (ValueError, OverflowError):
                break  # Error converting, stop
        else:
            break  # Not enough bits for a complete character, stop
    
    # Step 10: Display the decoded message
    print(f"Decoded secret message: {message}")


# Start the program
main()