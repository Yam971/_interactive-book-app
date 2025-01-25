import os
import re
from PIL import Image

def generate_progressive_images(child_name, config):
    name_length = len(child_name)
    if name_length < 2:
        return []

    def generate_partial_image(substr, step_index):
        # ========== DYNAMIC BACKGROUND ==========
        next_char = child_name[step_index].upper() if step_index < len(child_name) else None
        bg_dir = os.path.join(
            os.path.dirname(__file__),
            config["paths"]["renoir_background_dir"].replace("renoir_V0_1/", "")
        )
        
        bg_file = (
            "Background_hyphen.png" if next_char == '-' else
            f"Background_{next_char}.png" if next_char else
            "Background.png"
        )
        bg_path = os.path.join(bg_dir, bg_file)
        
        if not os.path.exists(bg_path):
            bg_path = os.path.join(bg_dir, "Background.png")

        try:
            background = Image.open(bg_path).convert("RGBA")
        except Exception as e:
            print(f"Background error: {str(e)}")
            background = Image.new("RGBA", (1200, 800), (255,255,255,0))

        # ========== CRITICAL ALIGNMENT FIXES ==========
        substring_len = len(substr)
        spacing = config["letter_spacing_per_length"].get(
            str(substring_len), 
            config["default_letter_spacing_px"]
        )

        # Load letter variations
        letters_folder_key = (
            "renoir_letters_small" if 8 <= substring_len <= 12 
            else "renoir_letters_normal"
        )
        letters_folder = os.path.join(
            os.path.dirname(__file__),
            config["paths"][letters_folder_key].replace("renoir_V0_1/", "")
        )

        variations_cache = {}
        def get_variations(char):
            base = 'hyphen' if char == '-' else char.upper()
            suffix = "_small" if 8 <= substring_len <= 12 else ""
            pattern = re.compile(rf"^{re.escape(base)}(\d+)?{suffix}\.png$")
            return sorted(
                [f for f in os.listdir(letters_folder) if pattern.match(f)],
                key=lambda x: int(x[len(base):-4]) if x[len(base):-4].isdigit() else 0
            )

        def load_variation(char):
            if char not in variations_cache:
                variations_cache[char] = (get_variations(char), 0)
            files, idx = variations_cache[char]
            if not files:
                return None
            chosen = files[idx % len(files)]
            variations_cache[char] = (files, idx + 1)
            return Image.open(os.path.join(letters_folder, chosen)).convert("RGBA")

        # ========== PROPER WIDTH CALCULATION ==========
        images = [load_variation(c) for c in substr if load_variation(c)]
        if not images:
            return None

        # Calculate total width with CORRECT spacing
        total_letter_width = sum(img.width for img in images)
        total_spacing = spacing * (len(images) - 1)
        total_width = total_letter_width + total_spacing

        # Center alignment
        x_start = (background.width - total_width) // 2
        current_x = x_start

        # Composite letters with consistent spacing
        for img in images:
            background.alpha_composite(img, (current_x, 0))
            current_x += img.width + spacing  # Match spacing used in calculation

        # Save output
        output_folder = os.path.join(
            os.path.dirname(__file__),
            config["paths"]["renoir_output"].replace("renoir_V0_1/", "")
        )
        os.makedirs(output_folder, exist_ok=True)
        
        output_filename = f"Renoir_{child_name}_step{step_index}.png"
        background.save(os.path.join(output_folder, output_filename))
        
        return output_filename

    return [generate_partial_image(child_name[:i], i) for i in range(1, name_length) if child_name[:i]]