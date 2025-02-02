import os
import time
from PIL import Image

_renoir_backgrounds = {}
_renoir_letter_variations = {}

_monet_backgrounds = {}
_monet_letter_variations = {}

_caching_info = {
    "is_cached": False,
    "total_images": 0,
    "time_seconds": 0.0,
    "validation_report": []
}

def init_cache(config):
    print("Hello, I am here!")
    global _caching_info
    if _caching_info["is_cached"]:
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

    # Build the validation report
    _caching_info["validation_report"] = _validate_caching()

    print(f"[Info] Caching complete. {total_images} images loaded in {duration:.2f} seconds.")
    return _caching_info

def _preload_renoir_assets(config):
    count = 0
    background_dir = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["renoir_background_dir"]
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

    normal_letters_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["renoir_letters_normal"]
    )
    small_letters_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["renoir_letters_small"]
    )

    print(f"[Debug] Renoir normal_letters_path: {normal_letters_path}")
    _debug_preload_letter_folder(normal_letters_path, _renoir_letter_variations, "[Renoir Normal]")

    print(f"[Debug] Renoir small_letters_path: {small_letters_path}")
    _debug_preload_letter_folder(small_letters_path, _renoir_letter_variations, "[Renoir Small]")

    count += _debug_preload_letter_folder(normal_letters_path, _renoir_letter_variations,
                                          count_label="[Renoir Normal]", do_load=True)
    count += _debug_preload_letter_folder(small_letters_path, _renoir_letter_variations,
                                          count_label="[Renoir Small]", do_load=True)
    return count

def _preload_monet_assets(config):
    count = 0
    bg_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["new_background"]
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

    normal_letters_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["letters_normal"]
    )
    small_letters_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["letters_small"]
    )

    print(f"[Debug] Monet normal_letters_path: {normal_letters_path}")
    print(f"[Debug] Monet small_letters_path: {small_letters_path}")

    count += _debug_preload_letter_folder(normal_letters_path, _monet_letter_variations,
                                          count_label="[Monet Normal]", do_load=True)
    count += _debug_preload_letter_folder(small_letters_path, _monet_letter_variations,
                                          count_label="[Monet Small]", do_load=True)
    return count

def _debug_preload_letter_folder(folder_path, variations_dict, count_label="", do_load=False):
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

def _validate_caching():
    """
    Returns a list of lines describing each image-type check.
    If it matches, we add "✅"; if not, we add a red "❌".
    """
    report_lines = []
    combined_backgrounds = set(_renoir_backgrounds.keys()).union(_monet_backgrounds.keys())
    combined_letters = set(_renoir_letter_variations.keys()).union(_monet_letter_variations.keys())

    # We'll define a small helper:
    def check_ok(condition):
        # Returns " ✅" if condition is True, else " <span style='color:red'>❌</span>"
        return " ✅" if condition else " <span style='color:red'>❌</span>"

    import re

    # A) Letter-Specific BGs: 26 expected
    letter_specific_count = 0
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        fname = f"Background_{ch}.png"
        if fname in combined_backgrounds:
            letter_specific_count += 1
    cond_a = (letter_specific_count == 26)
    line_a = f"Letter-Specific Backgrounds: total validated ({letter_specific_count}/26)"
    line_a += check_ok(cond_a)
    report_lines.append(line_a)

    # B) Alternate BGs => match "Background_[A-Z]\d+\.png"
    alt_pattern = re.compile(r"^Background_[A-Z]\d+\.png$")
    alt_count = sum(1 for fname in combined_backgrounds if alt_pattern.match(fname))
    cond_b = (alt_count > 0)  # no fixed total
    line_b = f"Alternate Letter-Specific Backgrounds: total validated ({alt_count} images)"
    line_b += check_ok(cond_b)  # we only show a check if at least 1 found
    report_lines.append(line_b)

    # C) Fallback BG => "Background_fallback.png", expected 1
    fallback_exists = ("Background_fallback.png" in combined_backgrounds)
    cond_c = fallback_exists
    line_c = f"Fallback Background: total validated ("
    line_c += "1/1" if fallback_exists else "0/1"
    line_c += ")" + check_ok(cond_c)
    report_lines.append(line_c)

    # D) Hyphen BG => "Background_hyphen.png", expected 1
    hyphen_exists = ("Background_hyphen.png" in combined_backgrounds)
    cond_d = hyphen_exists
    line_d = f"Hyphen Background: total validated ("
    line_d += "1/1" if hyphen_exists else "0/1"
    line_d += ")" + check_ok(cond_d)
    report_lines.append(line_d)

    # E) Default => "Background.png", expected 1
    default_exists = ("Background.png" in combined_backgrounds)
    cond_e = default_exists
    line_e = f"Default Background: total validated ("
    line_e += "1/1" if default_exists else "0/1"
    line_e += ")" + check_ok(cond_e)
    report_lines.append(line_e)

    # F) Standard Letters => A..Z => expected 26
    std_count = 0
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        fname = f"{ch}.png"
        if fname in combined_letters:
            std_count += 1
    cond_f = (std_count == 26)
    line_f = f"Standard Letter Images: total validated ({std_count}/26)"
    line_f += check_ok(cond_f)
    report_lines.append(line_f)

    # G) Small Letters => A_small..Z_small => expected 26
    small_count = 0
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        fname = f"{ch}_small.png"
        if fname in combined_letters:
            small_count += 1
    cond_g = (small_count == 26)
    line_g = f"Small Letter Images: total validated ({small_count}/26)"
    line_g += check_ok(cond_g)
    report_lines.append(line_g)

    # H) Small Hyphen => "hyphen_small.png", expected 1
    small_hyphen_exists = ("hyphen_small.png" in combined_letters)
    cond_h = small_hyphen_exists
    line_h = f"Small Hyphen Image: total validated ("
    line_h += "1/1" if small_hyphen_exists else "0/1"
    line_h += ")" + check_ok(cond_h)
    report_lines.append(line_h)

    return report_lines
