# gui/utils.py
from pathlib import Path
from PIL import Image
import customtkinter as ctk
from config import ASSETS_PATH  # берём из config

# from config import ASSETS_PATH  # !!!  Используем из config

# !!!  Больше не нужно
# _ASSETS_PATH = Path(__file__).parent.parent.resolve() / "assets/frame0"


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


def load_icon(name: str, size=(24, 24)):
    img = Image.open(relative_to_assets(name))
    return ctk.CTkImage(img, size=size)
