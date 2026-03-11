import io
import cv2
import numpy as np
from PIL import Image
from rembg import remove

def process_sticker(input_image_bytes):
    """
    1. Removes background
    2. Smoothes details
    3. Adds a white border
    4. Resizes to 512x512 max
    5. Returns an io.BytesIO containing a .webp sticker
    """
    # 1. Background removal using U2Net model (rembg default)
    result_bytes = remove(input_image_bytes)
    img_pil = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
    
    # Convert to OpenCV format
    img_cv = np.array(img_pil)
    b, g, r, alpha = cv2.split(img_cv)
    rgb = cv2.merge([b, g, r])
    
    # 2. Simplify image colors and details
    smoothed_rgb = cv2.bilateralFilter(rgb, d=9, sigmaColor=75, sigmaSpace=75)
    
    # 3. Add white border
    # Threshold alpha to create a solid mask
    _, alpha_thresh = cv2.threshold(alpha, 127, 255, cv2.THRESH_BINARY)
    
    # Create a dilated contour around the shape
    max_dim = max(img_cv.shape[0], img_cv.shape[1])
    kernel_size = max(5, int(max_dim * 0.025)) # ~2.5% of max dimension 
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    
    dilated_alpha = cv2.dilate(alpha_thresh, kernel, iterations=1)
    
    # Smooth the outline slightly
    dilated_alpha = cv2.GaussianBlur(dilated_alpha, (kernel_size | 1, kernel_size | 1), 0)
    _, dilated_alpha = cv2.threshold(dilated_alpha, 127, 255, cv2.THRESH_BINARY)
    
    # 4. Construct final RGBA image (Alpha Blending FG over BG)
    # The background is solid white where dilated_alpha > 0
    bg = np.zeros_like(img_cv)
    bg[..., 0:3] = 255
    bg[..., 3] = dilated_alpha
    
    # The foreground is the smoothed RGB + original alpha
    fg = np.zeros_like(img_cv)
    fg[..., 0:3] = smoothed_rgb
    fg[..., 3] = alpha
    
    # Normalize alphas for blending
    fg_a = fg[..., 3].astype(np.float32) / 255.0
    bg_a = bg[..., 3].astype(np.float32) / 255.0
    
    # Perform alpha blending
    out = np.zeros_like(img_cv, dtype=np.float32)
    out_a = fg_a + bg_a * (1 - fg_a)
    
    # Blend RGB channels
    out[..., 0:3] = fg[..., 0:3] * fg_a[..., None] + bg[..., 0:3] * bg_a[..., None] * (1 - fg_a[..., None])
    
    # Normalize RGB appropriately, avoid division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        out[..., 0:3] /= out_a[..., None]
    
    out[np.isnan(out)] = 0
    out[..., 3] = out_a * 255.0
    
    out = np.clip(out, 0, 255).astype(np.uint8)
    
    # Convert back to PIL Image
    final_pil = Image.fromarray(out, "RGBA")
    
    # 5. Resize to fit 512x512 max limit for Telegram stickers
    width, height = final_pil.size
    
    # Calculate new dimensions mapping the largest side to 512 exactly
    if width >= height:
        new_width = 512
        new_height = int((512 / width) * height)
    else:
        new_height = 512
        new_width = int((512 / height) * width)
        
    resized_pil = final_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 6. Save as .webp format
    output_buffer = io.BytesIO()
    # Provide name ending in .webp so Telegram realizes it's a sticker
    output_buffer.name = "sticker.webp" 
    
    resized_pil.save(output_buffer, format="WEBP")
    output_buffer.seek(0)
    
    return output_buffer
