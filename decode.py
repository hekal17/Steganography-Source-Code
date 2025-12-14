from encode import validate_bmp_basic, read_bmp_header, read_image_file, validate_bmp_header


def extract_bits_24bit(img_bytes, pixel_data_offset, delimiter, header_info):
    """Extracts hidden bits from a 24-bit BMP image using smart pixel looping.
    
    Args:
        img_bytes (bytearray): The image file bytes.
        pixel_data_offset (int): Offset where pixel data starts.
        delimiter (str): The delimiter pattern to look for (marks end of message).
        header_info (dict): Header information from read_bmp_header().
    
    Returns:
        str: Extracted binary string (including delimiter if found), or None if error.
    """
    extracted_bits = ""
    width = header_info['width']
    height = header_info['height']
    
    # In a 24-bit image, each pixel uses 3 bytes (one for Blue, one for Green, one for Red)
    bytes_per_pixel = 3
    
    # Calculate how many bytes are in one row (without padding)
    bytes_per_row_without_padding = width * bytes_per_pixel
    
    # BMP files require each row to be a multiple of 4 bytes
    # Calculate how many bytes per row including padding
    remainder = bytes_per_row_without_padding % 4
    if remainder == 0:
        # Already a multiple of 4, no padding needed
        bytes_per_row = bytes_per_row_without_padding
    else:
        # Need to add padding to make it a multiple of 4
        padding_needed = 4 - remainder
        bytes_per_row = bytes_per_row_without_padding + padding_needed
    
    # Get the number of rows (use absolute value in case height is negative)
    if height < 0:
        number_of_rows = -height
    else:
        number_of_rows = height
    
    # Extract bits using smart pixel looping (matching the encoding method)
    # We iterate row by row, pixel by pixel, and skip padding bytes
    for row in range(number_of_rows):
        # Calculate where this row starts in the file
        row_start = pixel_data_offset + (row * bytes_per_row)
        
        # Go through each pixel in this row
        for pixel in range(width):
            # Calculate where this pixel starts in the file
            pixel_start = row_start + (pixel * bytes_per_pixel)
            
            # Each pixel has 3 color channels: Blue (0), Green (1), and Red (2)
            # We'll read one bit from each channel
            for channel in range(3):
                # Calculate which byte we're reading from
                byte_index = pixel_start + channel
                
                # Make sure we don't go past the end of the file
                if byte_index >= len(img_bytes):
                    break
                
                # Get the last bit of this byte
                # 0b00000001 in binary means only the last bit is 1
                # When we use & (AND), it gives us just the last bit
                last_bit = img_bytes[byte_index] & 0b00000001
                
                # Convert the bit (which is 0 or 1) to a string and add it to our extracted bits
                extracted_bits = extracted_bits + str(last_bit)
                
                # Check if we've found the delimiter (the end of the message)
                if len(extracted_bits) >= len(delimiter):
                    # Get the last few bits (same length as delimiter)
                    start_index = len(extracted_bits) - len(delimiter)
                    last_bits = extracted_bits[start_index:]
                    
                    # Check if they match our delimiter
                    if last_bits == delimiter:
                        return extracted_bits  # Found the end!
    
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
    
    # For 32-bit images, each pixel has 4 bytes: Blue, Green, Red, and Alpha
    # We'll skip the Alpha channel and only read from Blue, Green, and Red
    # Start at the pixel data and go through each pixel (every 4 bytes)
    pixel_start = pixel_data_offset
    while pixel_start < len(img_bytes):
        # For each pixel, read from the first 3 bytes (Blue, Green, Red)
        # We skip the 4th byte (Alpha channel)
        for channel in range(3):  # 0=Blue, 1=Green, 2=Red
            # Calculate which byte we're reading from
            byte_index = pixel_start + channel
            
            # Make sure we don't go past the end of the file
            if byte_index >= len(img_bytes):
                break
            
            # Get the last bit of this byte
            # 0b00000001 in binary means only the last bit is 1
            # When we use & (AND), it gives us just the last bit
            last_bit = img_bytes[byte_index] & 0b00000001
            
            # Convert the bit (which is 0 or 1) to a string and add it to our extracted bits
            extracted_bits = extracted_bits + str(last_bit)
            
            # Check if we've found the delimiter (the end of the message)
            if len(extracted_bits) >= len(delimiter):
                # Get the last few bits (same length as delimiter)
                start_index = len(extracted_bits) - len(delimiter)
                last_bits = extracted_bits[start_index:]
                
                # Check if they match our delimiter
                if last_bits == delimiter:
                    return extracted_bits  # Found the end!
        
        # Move to the next pixel (each pixel is 4 bytes)
        pixel_start = pixel_start + 4
    
    return extracted_bits


def validate_extracted_bits(extracted_bits, delimiter):
    """Validates that extracted bits contain a valid message with delimiter.
    
    Args:
        extracted_bits (str): The extracted binary string.
        delimiter (str): The delimiter pattern to look for.
    
    Returns:
        bool: True if valid message found, False otherwise.
    """
    # Check if we found enough bits to have a delimiter
    delimiter_length = len(delimiter)
    if len(extracted_bits) < delimiter_length:
        print("Error: No valid hidden message found in this image.")
        return False
    
    # Get the last few bits (same length as delimiter)
    start_index = len(extracted_bits) - delimiter_length
    last_bits = extracted_bits[start_index:]
    
    # Check if the last bits match our delimiter
    if last_bits != delimiter:
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
    # Go through the message 8 bits at a time
    i = 0
    while i < len(message_bits):
        # Get the next 8 bits
        # For example, if i=0, we get bits 0-7
        # If i=8, we get bits 8-15, etc.
        end_index = i + 8
        byte_bits = message_bits[i:end_index]
        
        # Make sure we have exactly 8 bits
        if len(byte_bits) == 8:
            try:
                # Convert binary string to a number
                # The '2' means we're converting from base 2 (binary)
                # For example, '01000001' becomes 65
                char_code = int(byte_bits, 2)
                
                # Make sure it's a valid character code
                # Unicode characters can have codes from 0 to 1114111
                if char_code >= 0 and char_code <= 1114111:
                    # Convert the number to a character
                    # For example, 65 becomes 'A'
                    char = chr(char_code)
                    message = message + char
                else:
                    break  # Invalid character code, stop
            except (ValueError, OverflowError):
                break  # Error converting, stop
        else:
            break  # Not enough bits for a complete character, stop
        
        # Move to the next 8 bits
        i = i + 8
    
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
        extracted_bits = extract_bits_24bit(img_bytes, pixel_data_offset, delimiter, header_info)
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