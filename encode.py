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
    # Ask them how they want to provide it - typing directly or from a file
    print("\nHow would you like to provide the secret message?")
    print("1. Type the message directly")
    print("2. Provide a path to a text file")
    
    message_choice = input("Enter your choice (1 or 2): ").strip()
    secret_text = ""  # This will hold the message we want to hide
    
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
            return
        except Exception as e:
            # Some other error happened (permissions, encoding, etc.)
            print(f"Error: Could not read the text file '{text_file_path}'. {str(e)}")
            return
    else:
        # User entered something other than 1 or 2
        print("Invalid choice. Please enter 1 or 2.")
        return
    
    # Make sure we actually have a message to hide
    if not secret_text:
        print("Error: Secret message cannot be empty.")
        return
    
    # Step 2: Get the image file from the user
    image_file_path = input("Please enter the path to the BMP image file: ")
    
    # Step 3: Read the image file
    # We need to open it in binary mode ('rb') because images are binary files
    try:
        img_file = open(image_file_path, 'rb')  # 'rb' = read binary
        img_bytes = bytearray(img_file.read())   # Read all bytes and make it modifiable
        img_file.close()  # Close the file
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
    
    # Step 4: Check if it's actually a BMP file
    # BMP files always start with the letters 'BM' - that's how you identify them
    if img_bytes[0:2] != b'BM':
        print(f"Error: The file '{image_file_path}' is not a valid BMP file.")
        print("BMP files must start with 'BM'. Please use an uncompressed 24-bit or 32-bit BMP image.")
        return
    
    # Step 5: Check if the file is big enough to have a valid header
    # BMP headers are at least 54 bytes long - if the file is smaller, it's corrupted
    if len(img_bytes) < 54:
        print("Error: BMP file header is too small or corrupted.")
        return
    
    # Step 6: Convert the secret message to binary
    # Computers store everything as binary (ones and zeros)
    # Each character in our message needs to become 8 bits of binary data
    binary_message = ""
    for char in secret_text:
        try:
            # ord() gets the number that represents this character (like ASCII code)
            # format(..., '08b') converts that number to 8-bit binary with leading zeros
            # For example: 'A' becomes 65, which becomes '01000001'
            char_binary = format(ord(char), '08b')
            binary_message = binary_message + char_binary
        except (TypeError, ValueError):
            print("Error: Invalid character in message. Please use standard text characters.")
            return
    
    # Step 7: Add a delimiter to mark where the message ends
    # This is a special pattern: 0000000000000001 (16 zeros then a 1)
    # When we decode later, we'll look for this pattern to know when to stop reading
    # It's like putting a bookmark at the end of our message
    delimiter = '0000000000000001'
    full_data = binary_message + delimiter
    
    # Step 8: Read information from the BMP header
    # The header is the first part of the file and tells us important things:
    # - Where the pixel data starts
    # - How many bits per pixel (24 or 32)
    # - Whether it's compressed
    # - The image width and height
    
    # Find where the pixel data starts (this is stored in bytes 10-13 of the header)
    try:
        pixel_data_offset = int.from_bytes(img_bytes[10:14], byteorder='little')
    except (ValueError, IndexError):
        print("Error: Could not read pixel data offset from BMP header. File may be corrupted.")
        return
    
    # Make sure the offset makes sense
    if pixel_data_offset < 54:
        print("Error: Invalid pixel data offset in BMP header.")
        return
    if pixel_data_offset > len(img_bytes):
        print("Error: Pixel data offset is beyond the file size.")
        return
    
    # Check if the image is compressed
    # We only support uncompressed BMP files (compression type = 0)
    # This information is stored in bytes 30-33
    try:
        compression = int.from_bytes(img_bytes[30:34], byteorder='little')
    except (ValueError, IndexError):
        print("Error: Could not read compression type from BMP header. File may be corrupted.")
        return
    if compression != 0:
        print("Error: Only uncompressed BMP files are supported.")
        return
    
    # Find out how many bits per pixel
    # This tells us if it's 24-bit (3 bytes per pixel) or 32-bit (4 bytes per pixel)
    # This is stored in bytes 28-29
    try:
        bits_per_pixel = int.from_bytes(img_bytes[28:30], byteorder='little')
    except (ValueError, IndexError):
        print("Error: Could not read bits per pixel from BMP header. File may be corrupted.")
        return
    
    # Step 9: Hide the message in the image
    # We handle 24-bit and 32-bit images differently because they store pixels differently
    
    if bits_per_pixel == 24:
        # 24-bit images: Each pixel has 3 bytes (Blue, Green, Red)
        # Note: BMP stores colors as BGR, not RGB!
        
        # Get the image width and height (stored in bytes 18-21 for width, 22-25 for height)
        try:
            width = int.from_bytes(img_bytes[18:22], byteorder='little')
            height = int.from_bytes(img_bytes[22:26], byteorder='little', signed=True)
        except (ValueError, IndexError):
            print("Error: Could not read image dimensions from BMP header. File may be corrupted.")
            return
        # Height can be negative (means image is stored top-to-bottom instead of bottom-to-top)
        
        # Validate the dimensions
        if width <= 0:
            print(f"Error: Invalid image width ({width}). Width must be greater than 0.")
            return
        if height == 0:
            print(f"Error: Invalid image height ({height}). Height cannot be zero.")
            return
        
        # Calculate how much space we have to hide our message
        # BMP rows must be a multiple of 4 bytes, so there might be padding bytes
        # We need to account for this when calculating available space
        bytes_per_pixel = 3  # 24-bit = 3 bytes per pixel
        bytes_per_row_without_padding = width * bytes_per_pixel
        
        # Round up to the nearest multiple of 4 (this is the padding requirement)
        bytes_per_row = ((bytes_per_row_without_padding + 3) // 4) * 4
        
        # Calculate total number of bytes in all rows
        number_of_rows = abs(height)  # Use absolute value since height might be negative
        total_pixel_bytes = bytes_per_row * number_of_rows
        
        # Also check how many bytes are actually in the file (to be safe)
        actual_available_bytes = len(img_bytes) - pixel_data_offset
        
        # Use whichever is smaller (to be safe)
        available_bits = min(total_pixel_bytes, actual_available_bytes)
        
        # Check if our message will fit
        if len(full_data) > available_bits:
            message_size = len(full_data)
            print(f"Error: The message is too long for this image.")
            print(f"Message requires {message_size} bits, but image only has {available_bits} bits available.")
            print(f"Try using a larger image or a shorter message.")
            return
        
        # Now hide each bit of our message in the image
        # We go through each bit and change the last bit of each byte
        for bit_position in range(len(full_data)):
            # Calculate which byte in the image we're modifying
            byte_index = pixel_data_offset + bit_position
            
            # Make sure we don't try to write beyond the end of the file
            if byte_index >= len(img_bytes):
                print("Error: Attempted to write beyond file size. Image may be corrupted.")
                return
            
            # Get the current byte value
            current_byte = img_bytes[byte_index]
            
            # Clear the last bit (set it to 0) using bitwise AND with 11111110
            # This preserves all the other bits, just clears the last one
            cleared_byte = current_byte & 0b11111110
            
            # Set the last bit to our message bit using bitwise OR
            try:
                message_bit = int(full_data[bit_position])  # Convert '0' or '1' to integer
            except (ValueError, IndexError):
                print("Error: Invalid data format. This should not happen.")
                return
            new_byte = cleared_byte | message_bit  # Combine cleared byte with our bit
            
            # Update the byte in the image
            img_bytes[byte_index] = new_byte
    
    elif bits_per_pixel == 32:
        # 32-bit images: Each pixel has 4 bytes (Blue, Green, Red, Alpha)
        # We'll use the first 3 bytes (B, G, R) and skip the Alpha channel
        # Alpha is for transparency, and we don't want to mess with that
        
        # Get the image dimensions
        try:
            width = int.from_bytes(img_bytes[18:22], byteorder='little')
            height = int.from_bytes(img_bytes[22:26], byteorder='little', signed=True)
        except (ValueError, IndexError):
            print("Error: Could not read image dimensions from BMP header. File may be corrupted.")
            return
        
        # Validate dimensions
        if width <= 0:
            print(f"Error: Invalid image width ({width}). Width must be greater than 0.")
            return
        if height == 0:
            print(f"Error: Invalid image height ({height}). Height cannot be zero.")
            return
        
        # Calculate available space
        # Each pixel has 4 bytes, we use 3 of them (skip Alpha)
        number_of_rows = abs(height)
        total_pixels = number_of_rows * width
        available_bits = total_pixels * 3  # 3 bytes per pixel we can use
        
        # Also check actual file size (to be safe)
        actual_available_bytes = len(img_bytes) - pixel_data_offset
        available_bits_from_file = (actual_available_bytes // 4) * 3
        
        # Use the smaller value (to be safe)
        available_bits = min(available_bits, available_bits_from_file)
        
        # Check if message will fit
        if len(full_data) > available_bits:
            message_size = len(full_data)
            print(f"Error: The message is too long for this image.")
            print(f"Message requires {message_size} bits, but image only has {available_bits} bits available.")
            print(f"Try using a larger image or a shorter message.")
            return
        
        # Hide the message
        # We go through each pixel (every 4 bytes) and use the first 3 bytes
        data_index = 0  # Track which bit of our message we're currently hiding
        for pixel_start in range(pixel_data_offset, len(img_bytes), 4):
            # For each pixel, use the first 3 bytes (B, G, R)
            for channel in range(3):  # 0=Blue, 1=Green, 2=Red
                if data_index < len(full_data):
                    byte_index = pixel_start + channel
                    
                    # Make sure we don't go out of bounds
                    if byte_index >= len(img_bytes):
                        print("Error: Attempted to write beyond file size. Image may be corrupted.")
                        return
                    
                    # Get the current byte and modify its last bit
                    current_byte = img_bytes[byte_index]
                    cleared_byte = current_byte & 0b11111110  # Clear last bit
                    try:
                        message_bit = int(full_data[data_index])  # Get our message bit
                    except (ValueError, IndexError):
                        print("Error: Invalid data format. This should not happen.")
                        return
                    new_byte = cleared_byte | message_bit  # Set last bit to our message bit
                    img_bytes[byte_index] = new_byte  # Update the byte
                    data_index = data_index + 1  # Move to next bit
                else:
                    break  # We've hidden all our data
            if data_index >= len(full_data):
                break  # Stop if we're done
    
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
    
    # Step 10: Save the modified image
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
    except PermissionError:
        print(f"Error: Permission denied. Cannot write to: {new_image_path}")
        print("Please check file permissions or choose a different location.")
        return
    except Exception as e:
        print(f"Error: Could not save the image file '{new_image_path}'. {str(e)}")
        return