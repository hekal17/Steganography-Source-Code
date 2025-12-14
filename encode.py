def get_secret_message():
    """Gets the secret message from the user either by direct input or from a file.
    
    Returns:
        str: The secret message text, or None if there was an error or empty message.
    """
    print("\nHow would you like to provide the secret message?")
    print("1. Type the message directly")
    print("2. Provide a path to a text file")
    
    message_choice = input("Enter your choice (1 or 2): ").strip()
    secret_text = ""
    
    if message_choice == '1':
        # User wants to type the message themselves
        secret_text = input("Please enter the secret message: ")
        
    elif message_choice == '2':
        # User wants to read the message from a text file
        text_file_path = input("Please enter the path to the text file: ").strip()
        
        # Try to open and read the file
        try:
            text_file = open(text_file_path, 'r', encoding='utf-8')
            secret_text = text_file.read()  # Read everything in the file
            text_file.close()  # Always close files when done
        except FileNotFoundError:
            # The file doesn't exist at that path
            print(f"Error: Text file was not found at: {text_file_path}")
            print("Please check the file path and try again.")
            return None
        except Exception as e:
            # Some other error happened (permissions, encoding, etc.)
            print(f"Error: Could not read the text file '{text_file_path}'. {str(e)}")
            return None
    else:
        # User entered something other than 1 or 2
        print("Invalid choice. Please enter 1 or 2.")
        return None
    
    # Make sure we actually have a message to hide
    if not secret_text:
        print("Error: Secret message cannot be empty.")
        return None
    
    return secret_text


def read_image_file(image_file_path):
    # Reads a BMP image file from disk.

    try:
        img_file = open(image_file_path, 'rb')  # 'rb' = read binary
        img_bytes = bytearray(img_file.read())   # Read all bytes and make it modifiable
        img_file.close()  # Close the file
        return img_bytes
    except FileNotFoundError:
        print(f"Error: Image file was not found at: {image_file_path}")
        print("Please check the file path and try again.")
        return None
    except PermissionError:
        print(f"Error: Permission denied. Cannot read the file: {image_file_path}")
        return None
    except Exception as e:
        print(f"Error: Could not read the image file. {str(e)}")
        return None


def validate_bmp_basic(img_bytes, image_file_path):
    # Performs basic validation on a BMP file.

    # Check if it's actually a BMP file
    # BMP files always start with the letters 'BM' - that's how you identify them
    if img_bytes[0:2] != b'BM':
        print(f"Error: The file '{image_file_path}' is not a valid BMP file.")
        print("BMP files must start with 'BM'. Please use an uncompressed 24-bit or 32-bit BMP image.")
        return False
    
    # Check if the file is big enough to have a valid header
    # BMP headers are at least 54 bytes long - if the file is smaller, it's corrupted
    if len(img_bytes) < 54:
        print("Error: BMP file header is too small or corrupted.")
        return False
    
    return True


def read_bmp_header(img_bytes):
    # Reads and extracts information from the BMP file header.

    header_info = {}
    
    # Find where the pixel data starts (this is stored in bytes 10-13 of the header)
    try:
        # Get bytes 10, 11, 12, and 13
        offset_bytes = img_bytes[10:14]
        # Convert these 4 bytes to a number (little-endian means least significant byte first)
        header_info['pixel_data_offset'] = int.from_bytes(offset_bytes, byteorder='little')
    except (ValueError, IndexError):
        print("Error: Could not read pixel data offset from BMP header. File may be corrupted.")
        return None
    
    # Check if the image is compressed
    # We only support uncompressed BMP files (compression type = 0)
    # This information is stored in bytes 30-33
    try:
        # Get bytes 30, 31, 32, and 33
        compression_bytes = img_bytes[30:34]
        # Convert these 4 bytes to a number
        header_info['compression'] = int.from_bytes(compression_bytes, byteorder='little')
    except (ValueError, IndexError):
        print("Error: Could not read compression type from BMP header. File may be corrupted.")
        return None
    
    # Find out how many bits per pixel
    # This tells us if it's 24-bit (3 bytes per pixel) or 32-bit (4 bytes per pixel)
    # This is stored in bytes 28-29
    try:
        # Get bytes 28 and 29
        bits_bytes = img_bytes[28:30]
        # Convert these 2 bytes to a number
        header_info['bits_per_pixel'] = int.from_bytes(bits_bytes, byteorder='little')
    except (ValueError, IndexError):
        print("Error: Could not read bits per pixel from BMP header. File may be corrupted.")
        return None
    
    # Get the image width and height
    # Width is stored in bytes 18-21
    # Height is stored in bytes 22-25
    try:
        # Get bytes 18, 19, 20, and 21 for width
        width_bytes = img_bytes[18:22]
        header_info['width'] = int.from_bytes(width_bytes, byteorder='little')
        
        # Get bytes 22, 23, 24, and 25 for height
        # signed=True means the height can be negative (for top-down images)
        height_bytes = img_bytes[22:26]
        header_info['height'] = int.from_bytes(height_bytes, byteorder='little', signed=True)
    except (ValueError, IndexError):
        print("Error: Could not read image dimensions from BMP header. File may be corrupted.")
        return None
    
    return header_info


def validate_bmp_header(header_info, img_bytes):
    """Validates the BMP header information.
    
    Args:
        header_info (dict): Header information from read_bmp_header().
        img_bytes (bytearray): The image file bytes.
    
    Returns:
        bool: True if valid, False otherwise.
    """
    # Make sure the offset makes sense
    if header_info['pixel_data_offset'] < 54:
        print("Error: Invalid pixel data offset in BMP header.")
        return False
    if header_info['pixel_data_offset'] > len(img_bytes):
        print("Error: Pixel data offset is beyond the file size.")
        return False
    
    # Check if the image is compressed
    if header_info['compression'] != 0:
        print("Error: Only uncompressed BMP files are supported.")
        return False
    
    # Validate dimensions
    if header_info['width'] <= 0:
        print(f"Error: Invalid image width ({header_info['width']}). Width must be greater than 0.")
        return False
    if header_info['height'] == 0:
        print(f"Error: Invalid image height ({header_info['height']}). Height cannot be zero.")
        return False
    
    return True


def convert_message_to_binary(secret_text):
    """Converts a text message to binary format with a delimiter.
    
    Args:
        secret_text (str): The secret message text.
    
    Returns:
        str: Binary string representation of the message with delimiter, or None if error.
    """
    # Convert the secret message to binary
    # Computers store everything as binary (ones and zeros)
    # Each character in our message needs to become 8 bits of binary data
    binary_message = ""
    
    # Go through each character in the message
    for char in secret_text:
        try:
            # Get the number that represents this character (like ASCII code)
            # For example, 'A' has the code 65
            char_code = ord(char)
            
            # Convert that number to 8-bit binary with leading zeros
            # For example: 65 becomes '01000001'
            # The '08b' means: 8 digits, in binary format, with leading zeros
            char_binary = format(char_code, '08b')
            
            # Add this character's binary to our full binary message
            binary_message = binary_message + char_binary
        except (TypeError, ValueError):
            print("Error: Invalid character in message. Please use standard text characters.")
            return None
    
    # Add a delimiter to mark where the message ends
    # This is a special pattern: 0000000000000001 (15 zeros then a 1)
    # When we decode later, we'll look for this pattern to know when to stop reading
    # It's like putting a bookmark at the end of our message
    delimiter = '0000000000000001'
    
    # Combine the message and delimiter
    full_data = binary_message + delimiter
    
    return full_data


def encode_24bit(img_bytes, full_data, header_info):
    """Encodes a message into a 24-bit BMP image using LSB steganography.
    
    Args:
        img_bytes (bytearray): The image file bytes (will be modified).
        full_data (str): Binary string of the message with delimiter.
        header_info (dict): Header information from read_bmp_header().
    
    Returns:
        bool: True if successful, False otherwise.
    """
    # Get the information we need from the header
    pixel_data_offset = header_info['pixel_data_offset']
    width = header_info['width']
    height = header_info['height']
    
    # In a 24-bit image, each pixel uses 3 bytes (one for Blue, one for Green, one for Red)
    bytes_per_pixel = 3
    
    # Calculate how many bytes are in one row (without padding)
    bytes_per_row_without_padding = width * bytes_per_pixel
    
    # BMP files require each row to be a multiple of 4 bytes
    # So if a row is 10 bytes, we need to add 2 padding bytes to make it 12 bytes
    # Let's calculate how many bytes per row including padding
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
    
    # Calculate how many pixels are in the image
    total_pixels = number_of_rows * width
    
    # Each pixel has 3 bytes, and we can hide 1 bit in each byte
    # So we can hide 3 bits per pixel
    bits_per_pixel = 3
    available_bits = total_pixels * bits_per_pixel
    
    # Check if our message will fit
    message_length = len(full_data)
    if message_length > available_bits:
        print(f"Error: The message is too long for this image.")
        print(f"Message requires {message_length} bits, but image only has {available_bits} bits available.")
        print(f"Try using a larger image or a shorter message.")
        return False
    
    # Now we'll hide the message bit by bit
    # We'll go through each row, then each pixel, then each color channel
    data_index = 0  # This keeps track of which bit of our message we're currently hiding
    
    # Go through each row of the image
    for row in range(number_of_rows):
        # Calculate where this row starts in the file
        row_start = pixel_data_offset + (row * bytes_per_row)
        
        # Go through each pixel in this row
        for pixel in range(width):
            # Check if we've hidden all our data
            if data_index >= len(full_data):
                break  # We're done!
            
            # Calculate where this pixel starts in the file
            pixel_start = row_start + (pixel * bytes_per_pixel)
            
            # Each pixel has 3 color channels: Blue (0), Green (1), and Red (2)
            # We'll hide one bit in each channel
            for channel in range(3):
                # Check if we've hidden all our data
                if data_index >= len(full_data):
                    break  # We're done!
                
                # Calculate which byte we're modifying
                byte_index = pixel_start + channel
                
                # Make sure we don't go past the end of the file
                if byte_index >= len(img_bytes):
                    print("Error: Attempted to write beyond file size. Image may be corrupted.")
                    return False
                
                # Get the current byte value
                current_byte = img_bytes[byte_index]
                
                # Clear the last bit (set it to 0)
                # 0b11111110 in binary means all bits are 1 except the last one
                # When we use & (AND), it keeps all bits the same except sets the last bit to 0
                cleared_byte = current_byte & 0b11111110
                
                # Get the bit we want to hide (convert from string '0' or '1' to integer)
                message_bit_string = full_data[data_index]
                message_bit = int(message_bit_string)
                
                # Set the last bit to our message bit
                # When we use | (OR), it combines the cleared byte with our bit
                new_byte = cleared_byte | message_bit
                
                # Update the byte in the image
                img_bytes[byte_index] = new_byte
                
                # Move to the next bit of our message
                data_index = data_index + 1
        
        # Check if we're done (we skip padding bytes automatically because we only
        # iterate through 'width' pixels, not the full bytes_per_row)
        if data_index >= len(full_data):
            break  # We're done!
    
    return True


def encode_32bit(img_bytes, full_data, header_info):
    """Encodes a message into a 32-bit BMP image using LSB steganography.
    
    Args:
        img_bytes (bytearray): The image file bytes (will be modified).
        full_data (str): Binary string of the message with delimiter.
        header_info (dict): Header information from read_bmp_header().
    
    Returns:
        bool: True if successful, False otherwise.
    """
    # Get the information we need from the header
    pixel_data_offset = header_info['pixel_data_offset']
    width = header_info['width']
    height = header_info['height']
    
    # Get the number of rows (use absolute value in case height is negative)
    if height < 0:
        number_of_rows = -height
    else:
        number_of_rows = height
    
    # Calculate how many pixels are in the image
    total_pixels = number_of_rows * width
    
    # In a 32-bit image, each pixel has 4 bytes: Blue, Green, Red, and Alpha
    # We'll skip the Alpha channel and only use Blue, Green, and Red
    # So we can hide 3 bits per pixel
    bits_per_pixel = 3
    available_bits = total_pixels * bits_per_pixel
    
    # Check if our message will fit
    message_length = len(full_data)
    if message_length > available_bits:
        print(f"Error: The message is too long for this image.")
        print(f"Message requires {message_length} bits, but image only has {available_bits} bits available.")
        print(f"Try using a larger image or a shorter message.")
        return False
    
    # Now we'll hide the message bit by bit
    # We'll go through each pixel (every 4 bytes) and use the first 3 bytes
    data_index = 0  # This keeps track of which bit of our message we're currently hiding
    
    # Start at the pixel data and go through each pixel (every 4 bytes)
    pixel_start = pixel_data_offset
    while pixel_start < len(img_bytes):
        # For each pixel, we'll use the first 3 bytes (Blue, Green, Red)
        # We skip the 4th byte (Alpha channel)
        for channel in range(3):  # 0=Blue, 1=Green, 2=Red
            # Check if we've hidden all our data
            if data_index >= len(full_data):
                break  # We're done!
            
            # Calculate which byte we're modifying
            byte_index = pixel_start + channel
            
            # Make sure we don't go past the end of the file
            if byte_index >= len(img_bytes):
                print("Error: Attempted to write beyond file size. Image may be corrupted.")
                return False
            
            # Get the current byte value
            current_byte = img_bytes[byte_index]
            
            # Clear the last bit (set it to 0)
            # 0b11111110 in binary means all bits are 1 except the last one
            # When we use & (AND), it keeps all bits the same except sets the last bit to 0
            cleared_byte = current_byte & 0b11111110
            
            # Get the bit we want to hide (convert from string '0' or '1' to integer)
            message_bit_string = full_data[data_index]
            message_bit = int(message_bit_string)
            
            # Set the last bit to our message bit
            # When we use | (OR), it combines the cleared byte with our bit
            new_byte = cleared_byte | message_bit
            
            # Update the byte in the image
            img_bytes[byte_index] = new_byte
            
            # Move to the next bit of our message
            data_index = data_index + 1
        
        # Check if we're done
        if data_index >= len(full_data):
            break  # We're done!
        
        # Move to the next pixel (each pixel is 4 bytes)
        pixel_start = pixel_start + 4
    
    return True


def save_encoded_image(img_bytes):
    """Saves the encoded image to a file.
    
    Args:
        img_bytes (bytearray): The modified image file bytes.
    
    Returns:
        str: Path to the saved file, or None if there was an error.
    """
    # Ask the user what they want to name the new file
    new_image_path = input("Please enter the filename for the new image with .bmp extension (e.g., secret.bmp): ")
    
    # Make sure it ends with .bmp (add it if the user forgot)
    if not new_image_path.lower().endswith('.bmp'):
        new_image_path = new_image_path + '.bmp'
    
    # Write the file
    try:
        new_img_file = open(new_image_path, 'wb')  # 'wb' = write binary
        new_img_file.write(img_bytes)  # Write all the modified bytes
        new_img_file.close()  # Close the file
        print(f"Success! Your secret message has been encoded into {new_image_path}.")
        return new_image_path
    except PermissionError:
        print(f"Error: Permission denied. Cannot write to: {new_image_path}")
        print("Please check file permissions or choose a different location.")
        return None
    except Exception as e:
        print(f"Error: Could not save the image file '{new_image_path}'. {str(e)}")
        return None


def Encode():
    """This function hides a secret message inside a BMP image file.
    
    The steps go like this:
    1. Get the secret message from the user
    2. Get the image file to hide it in
    3. Convert the message to binary (ones and zeros)
    4. Read information from the BMP file header
    5. Hide each bit of the message in the image pixels
    6. Save the modified image
    
    We use LSB (Least Significant Bit) steganography - we change the last bit
    of each color channel byte to store our message. Since we only change the
    last bit, the image looks almost exactly the same to the human eye.
    """
    
    # Step 1: Get the secret message from the user
    secret_text = get_secret_message()
    if secret_text is None:
        return
    
    # Step 2: Get the image file from the user
    image_file_path = input("Please enter the path to the BMP image file: ")
    
    # Step 3: Read the image file
    img_bytes = read_image_file(image_file_path)
    if img_bytes is None:
        return
    
    # Step 4: Validate basic BMP structure
    if not validate_bmp_basic(img_bytes, image_file_path):
        return
    
    # Step 5: Read BMP header information
    header_info = read_bmp_header(img_bytes)
    if header_info is None:
        return
    
    # Step 6: Validate header information
    if not validate_bmp_header(header_info, img_bytes):
        return
    
    # Step 7: Convert the secret message to binary
    full_data = convert_message_to_binary(secret_text)
    if full_data is None:
        return
    
    # Step 8: Hide the message in the image based on bit depth
    bits_per_pixel = header_info['bits_per_pixel']
    
    if bits_per_pixel == 24:
        success = encode_24bit(img_bytes, full_data, header_info)
        if not success:
            return
    elif bits_per_pixel == 32:
        success = encode_32bit(img_bytes, full_data, header_info)
        if not success:
            return
    elif bits_per_pixel == 8:
        # 8-bit images use a color palette, which is more complicated
        print("Error: Encoding into 8-bit BMP images is not supported.")
        print("Please convert your image to a 24-bit or 32-bit BMP format.")
        return
    else:
        # Some other format we don't support
        print(f"Error: Unsupported BMP format. This image has {bits_per_pixel} bits per pixel.")
        print("Only 24-bit and 32-bit BMP images are supported.")
        return
    
    # Step 9: Save the modified image
    save_encoded_image(img_bytes)