import os
import time
from PIL import Image

# Module-level dictionaries to store cached images
_renoir_backgrounds = {}
_renoir_letter_variations = {}

_monet_backgrounds = {}
_monet_letter_variations = {}

# Store info about how many images were cached and how long it took
_caching_info = {
    "is_cached": False,
    "total_images": 0,
    "time_seconds": 0.0
}

def init_cache(config):
    """
    Loads all relevant background images & letter images for Renoir (and optionally Monet)
    into memory, if not already cached.
    Returns a dictionary with stats: how many images, how long it took, etc.
    """
    print("Hello, I am here!")  # Confirm function is actually called

    global _caching_info
    if _caching_info["is_cached"]:
        # Already cached, just return existing info
        print("[Debug] init_cache called, but cache is already initialized.")
        return _caching_info

    start_time = time.time()
    print("[Info] Starting cache initialization...")

    renoir_count = _preload_renoir_assets(config)
    monet_count = _preload_monet_assets(config)

    end_time = time.time()
    duration = end_time - start_time

    total_images = renoir_count + monet_count
    _caching_info["is_cached"] = True
    _caching_info["total_images"] = total_images
    _caching_info["time_seconds"] = round(duration, 2)

    print(f"[Info] Caching complete. {total_images} images loaded in {duration:.2f} seconds.")
    return _caching_info

def _preload_renoir_assets(config):
    """Load Renoir backgrounds and letter variations into memory with debug prints."""
    count = 0

    # 1) Renoir backgrounds
    background_dir = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["renoir_background_dir"]  # <--- removed .replace()
    )
    print(f"[Debug] Renoir background_dir: {background_dir}")

    if os.path.exists(background_dir):
        files_in_bg_dir = os.listdir(background_dir)
        print(f"[Debug] Files in renoir background_dir: {files_in_bg_dir}")
        for fname in files_in_bg_dir:
            if fname.lower().endswith(".png") and fname.startswith("Background"):
                path = os.path.join(background_dir, fname)
                try:
                    _renoir_backgrounds[fname] = Image.open(path).convert("RGBA")
                    count += 1
                    print(f"[Debug] Loaded Renoir background: {fname}")
                except Exception as e:
                    print(f"[Warning] Could not open Renoir background {fname}: {e}")
    else:
        print("[Warning] renoir_background_dir does not exist or is inaccessible.")

    # 2) Renoir letter variations (normal + small)
    normal_letters_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["renoir_letters_normal"]  # <--- removed .replace()
    )
    small_letters_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["renoir_letters_small"]   # <--- removed .replace()
    )

    print(f"[Debug] Renoir normal_letters_path: {normal_letters_path}")
    _debug_preload_letter_folder(normal_letters_path, _renoir_letter_variations, count_label="[Renoir Normal]")

    print(f"[Debug] Renoir small_letters_path: {small_letters_path}")
    _debug_preload_letter_folder(small_letters_path, _renoir_letter_variations, count_label="[Renoir Small]")

    # Actually load the images and add to count
    count += _debug_preload_letter_folder(normal_letters_path, _renoir_letter_variations,
                                          count_label="[Renoir Normal]", do_load=True)
    count += _debug_preload_letter_folder(small_letters_path, _renoir_letter_variations,
                                          count_label="[Renoir Small]", do_load=True)

    return count

def _preload_monet_assets(config):
    """Load Monet backgrounds (if desired) and letter variations into memory with debug prints."""
    count = 0

    # 1) Monet background
    bg_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["new_background"]  # <--- removed .replace()
    )
    print(f"[Debug] Monet background path: {bg_path}")

    if os.path.exists(bg_path):
        try:
            _monet_backgrounds["Background.png"] = Image.open(bg_path).convert("RGBA")
            count += 1
            print("[Debug] Loaded Monet background: Background.png")
        except Exception as e:
            print(f"[Warning] Could not open Monet background: {e}")
    else:
        print("[Warning] Monet background path does not exist or is inaccessible.")

    # 2) Letters (normal + small)
    normal_letters_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["letters_normal"]  # <--- removed .replace()
    )
    small_letters_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["letters_small"]   # <--- removed .replace()
    )

    print(f"[Debug] Monet normal_letters_path: {normal_letters_path}")
    print(f"[Debug] Monet small_letters_path: {small_letters_path}")

    count += _debug_preload_letter_folder(normal_letters_path, _monet_letter_variations,
                                          count_label="[Monet Normal]", do_load=True)
    count += _debug_preload_letter_folder(small_letters_path, _monet_letter_variations,
                                          count_label="[Monet Small]", do_load=True)

    return count

def _debug_preload_letter_folder(folder_path, variations_dict, count_label="", do_load=False):
    """
    Helper function to print debug info about a folder,
    optionally load .png images into variations_dict.
    Returns how many images were loaded.
    """
    loaded_count = 0
    if not os.path.exists(folder_path):
        print(f"{count_label} [Warning] Path does not exist: {folder_path}")
        return 0

    files_in_folder = os.listdir(folder_path)
    print(f"{count_label} [Debug] Files in {folder_path}: {files_in_folder}")

    if do_load:
        for fname in files_in_folder:
            if fname.lower().endswith(".png"):
                fullpath = os.path.join(folder_path, fname)
                try:
                    img = Image.open(fullpath).convert("RGBA")
                    variations_dict.setdefault(fname, []).append(img)
                    loaded_count += 1
                    print(f"{count_label} [Debug] Loaded letter image: {fname}")
                except Exception as e:
                    print(f"{count_label} [Warning] Could not open letter {fname}: {e}")

    return loaded_count
