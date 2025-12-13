from encode import validate_bmp_basic, read_bmp_header, read_image_file, validate_bmp_header


def extract_bits_24bit(img_bytes, pixel_data_offset, delimiter):
    """Extracts hidden bits from a 24-bit BMP image.
    
    Args:
        img_bytes (bytearray): The image file bytes.
        pixel_data_offset (int): Offset where pixel data starts.
        delimiter (str): The delimiter pattern to look for (marks end of message).
    
    Returns:
        str: Extracted binary string (including delimiter if found), or None if error.
    """
    extracted_bits = ""
    
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
    
    return extracted_bits


def extract_bits_32bit(img_bytes, pixel_data_offset, delimiter):
    """Extracts hidden bits from a 32-bit BMP image.
    
    Args:
        img_bytes (bytearray): The image file bytes.
        pixel_data_offset (int): Offset where pixel data starts.
        delimiter (str): The delimiter pattern to look for (marks end of message).
    
    Returns:
        str: Extracted binary string (including delimiter if found), or None if error.
    """
    extracted_bits = ""
    
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
    
    return extracted_bits


def validate_extracted_bits(extracted_bits, delimiter):
    """Validates that extracted bits contain a valid message with delimiter.
    
    Args:
        extracted_bits (str): The extracted binary string.
        delimiter (str): The delimiter pattern to look for.
    
    Returns:
        bool: True if valid message found, False otherwise.
    """
    # Check if we found a valid message
    if len(extracted_bits) < len(delimiter):
        print("Error: No valid hidden message found in this image.")
        return False
    
    # Check if the last bits match our delimiter
    last_16_bits = extracted_bits[-len(delimiter):]
    if last_16_bits != delimiter:
        print("Error: No valid hidden message found in this image.")
        return False
    
    return True


def convert_binary_to_text(message_bits):
    """Converts a binary string back to text.
    
    Args:
        message_bits (str): Binary string representing the message (without delimiter).
    
    Returns:
        str: The decoded text message.
    """
    message = ""
    
    # Each 8 bits represents one character
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
    
    return message


def Decode():
    """This function extracts a hidden message from a BMP image file."""
    
    # Step 1: Get the image file from the user
    image_file_path = input("Please enter the path to the BMP image file with hidden message: ")
    
    # Step 2: Read the image file
    img_bytes = read_image_file(image_file_path)
    if img_bytes is None:
        return
    
    # Step 3: Validate basic BMP structure
    if not validate_bmp_basic(img_bytes, image_file_path):
        return
    
    # Step 4: Read BMP header information
    header_info = read_bmp_header(img_bytes)
    if header_info is None:
        return
    
    # Step 5: Validate header information
    if not validate_bmp_header(header_info, img_bytes):
        return
    
    # Step 6: Extract the hidden bits
    # We'll look for our delimiter pattern to know when to stop
    delimiter = '0000000000000001'
    pixel_data_offset = header_info['pixel_data_offset']
    bits_per_pixel = header_info['bits_per_pixel']
    
    if bits_per_pixel == 24:
        extracted_bits = extract_bits_24bit(img_bytes, pixel_data_offset, delimiter)
    elif bits_per_pixel == 32:
        extracted_bits = extract_bits_32bit(img_bytes, pixel_data_offset, delimiter)
    elif bits_per_pixel == 8:
        print("Error: Decoding from 8-bit BMP images is not supported.")
        print("Please convert your image to a 24-bit or 32-bit BMP format.")
        return
    else:
        print(f"Error: Unsupported BMP format. This image has {bits_per_pixel} bits per pixel.")
        print("Only 24-bit and 32-bit BMP images are supported.")
        return
    
    # Step 7: Validate extracted bits
    if not validate_extracted_bits(extracted_bits, delimiter):
        return
    
    # Step 8: Remove the delimiter to get just the message bits
    message_bits = extracted_bits[:-len(delimiter)]
    
    # Step 9: Convert binary back to text
    message = convert_binary_to_text(message_bits)
    
    # Step 10: Display the decoded message
    print(f"Decoded secret message: {message}")