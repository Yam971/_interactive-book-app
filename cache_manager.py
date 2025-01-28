# cache_manager.py
import os
from PIL import Image

# We'll store these as module-level dictionaries.
_renoir_backgrounds = {}
_renoir_letter_variations = {}
_renoir_letter_variation_indexes = {}

_monet_backgrounds = {}
_monet_letter_variations = {}
_monet_letter_variation_indexes = {}

# Flag to indicate if we've already done a full init
_cache_initialized = False

def init_cache(config):
    """
    Loads all backgrounds and letter images for both Renoir and Monet into memory.
    If already loaded, this does nothing.
    """
    global _cache_initialized
    if _cache_initialized:
        print("[Info] Cache already initialized, skipping.")
        return

    print("[Info] Initializing cache...")
    _preload_renoir_assets(config)
    _preload_monet_assets(config)
    _cache_initialized = True
    print("[Info] Cache initialization complete.")


def _preload_renoir_assets(config):
    """
    Load Renoir background images + letter variations into memory.
    """
    # 1) Backgrounds
    background_dir = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["renoir_background_dir"].replace("renoir_V0_1/", "")
    )
    # We'll try to load all possible background files from that directory
    for fname in os.listdir(background_dir):
        if fname.lower().endswith(".png") and fname.startswith("Background"):
            path = os.path.join(background_dir, fname)
            try:
                _renoir_backgrounds[fname] = Image.open(path).convert("RGBA")
            except Exception as e:
                print(f"[Warning] Could not open Renoir background {fname}: {e}")

    # 2) Letters (normal + small)
    normal_letters_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["renoir_letters_normal"].replace("renoir_V0_1/", "")
    )
    small_letters_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["renoir_letters_small"].replace("renoir_V0_1/", "")
    )

    def preload_letter_folder(folder_path, use_small):
        if not os.path.exists(folder_path):
            return
        for fname in os.listdir(folder_path):
            if not fname.lower().endswith(".png"):
                continue
            fullpath = os.path.join(folder_path, fname)
            try:
                img = Image.open(fullpath).convert("RGBA")
                key = (fname, use_small)  # we'll store them by full filename + small flag
                _renoir_letter_variations[key] = _renoir_letter_variations.get(key, [])
                _renoir_letter_variations[key].append(img)
            except Exception as e:
                print(f"[Warning] Could not open Renoir letter {fname}: {e}")

    preload_letter_folder(normal_letters_path, use_small=False)
    preload_letter_folder(small_letters_path, use_small=True)


def _preload_monet_assets(config):
    """
    If desired, load Monet background images + letter variations into memory.
    If you only need Renoir, you can comment this out.
    """
    # 1) Background (only a single background for Monet_V0_8 in your code)
    bg_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["new_background"].replace("monet_V0_8/", "")
    )
    try:
        _monet_backgrounds["Background.png"] = Image.open(bg_path).convert("RGBA")
    except Exception as e:
        print(f"[Warning] Could not open Monet background: {e}")

    # 2) Letters (normal + small)
    normal_letters_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["letters_normal"].replace("monet_V0_8/", "")
    )
    small_letters_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["letters_small"].replace("monet_V0_8/", "")
    )

    def preload_letter_folder(folder_path, use_small):
        if not os.path.exists(folder_path):
            return
        for fname in os.listdir(folder_path):
            if not fname.lower().endswith(".png"):
                continue
            fullpath = os.path.join(folder_path, fname)
            try:
                img = Image.open(fullpath).convert("RGBA")
                key = (fname, use_small)
                _monet_letter_variations[key] = _monet_letter_variations.get(key, [])
                _monet_letter_variations[key].append(img)
            except Exception as e:
                print(f"[Warning] Could not open Monet letter {fname}: {e}")

    preload_letter_folder(normal_letters_path, use_small=False)
    preload_letter_folder(small_letters_path, use_small=True)
