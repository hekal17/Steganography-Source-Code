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
        print(f"Error: Image file was not found at: {image_file_path}")
        print("Please check the file path and try again.")
        return
    except PermissionError:
        print(f"Error: Permission denied. Cannot read the file: {image_file_path}")
        return
    except Exception as e:
        print(f"Error: Could not read the image file. {str(e)}")
        return
    
    # Step 3: Check if it's a BMP file
    if img_bytes[0:2] != b'BM':
        print(f"Error: The file '{image_file_path}' is not a valid BMP file.")
        print("BMP files must start with 'BM'. Please use an uncompressed 24-bit or 32-bit BMP image.")
        return
    
    # Step 4: Check header size
    if len(img_bytes) < 54:
        print("Error: BMP file header is too small or corrupted.")
        return
    
    # Step 5: Read BMP header information
    try:
        pixel_data_offset = int.from_bytes(img_bytes[10:14], byteorder='little')
    except (ValueError, IndexError):
        print("Error: Could not read pixel data offset from BMP header. File may be corrupted.")
        return
    
    if pixel_data_offset < 54:
        print("Error: Invalid pixel data offset in BMP header.")
        return
    if pixel_data_offset > len(img_bytes):
        print("Error: Pixel data offset is beyond the file size.")
        return
    
    # Check compression
    try:
        compression = int.from_bytes(img_bytes[30:34], byteorder='little')
    except (ValueError, IndexError):
        print("Error: Could not read compression type from BMP header. File may be corrupted.")
        return
    if compression != 0:
        print("Error: Only uncompressed BMP files are supported.")
        return
    
    # Get bits per pixel
    try:
        bits_per_pixel = int.from_bytes(img_bytes[28:30], byteorder='little')
    except (ValueError, IndexError):
        print("Error: Could not read bits per pixel from BMP header. File may be corrupted.")
        return
    
    # Step 6: Extract the hidden bits
    # We'll look for our delimiter pattern to know when to stop
    delimiter = '0000000000000001'
    extracted_bits = ""  # This will hold all the bits we extract
    
    
    
    if bits_per_pixel == 24:
        # For 24-bit images, read bits from every byte starting at pixel data
        for byte_index in range(pixel_data_offset, len(img_bytes)):
            # Make sure we don't go out of bounds (shouldn't happen, but be safe)
            if byte_index >= len(img_bytes):
                break
            
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
                
                # Make sure we don't go out of bounds
                if byte_index >= len(img_bytes):
                    break
                
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
        print("Please convert your image to a 24-bit or 32-bit BMP format.")
        return
    else:
        print(f"Error: Unsupported BMP format. This image has {bits_per_pixel} bits per pixel.")
        print("Only 24-bit and 32-bit BMP images are supported.")
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