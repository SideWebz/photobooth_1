from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps

from config import PHOTO_CARD_TEMPLATE, PHOTO_LAYOUT


def _fit_photo(path: str) -> Image.Image:
    """Crop en schaal een foto zonder vervorming naar het vaste fotovak."""
    with Image.open(path) as image:
        return ImageOps.fit(
            image.convert("RGB"),
            (PHOTO_LAYOUT["width"], PHOTO_LAYOUT["height"]),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )


def _photo_positions() -> tuple[dict[str, int], ...]:
    return tuple(PHOTO_LAYOUT[f"photo{index}"] for index in range(1, 4))


def _validate_layout(template: Image.Image) -> None:
    width = PHOTO_LAYOUT["width"]
    height = PHOTO_LAYOUT["height"]
    positions = _photo_positions()

    for position in positions:
        right = position["x"] + width
        bottom = position["y"] + height
        if position["x"] < 0 or position["y"] < 0 or right > template.width or bottom > template.height:
            raise ValueError("Photo layout does not fit inside PhotoCard.png")

    for previous, current in zip(positions, positions[1:]):
        actual_gap = current["y"] - (previous["y"] + height)
        if actual_gap != PHOTO_LAYOUT["gap"]:
            raise ValueError("Photo layout positions do not match the configured gap")


def _build_photo_card(photo_paths: tuple[str, ...]) -> Image.Image:
    with Image.open(PHOTO_CARD_TEMPLATE) as template_file:
        card = template_file.convert("RGBA")

    _validate_layout(card)

    for photo_path, position in zip(photo_paths, _photo_positions()):
        card.paste(_fit_photo(photo_path), (position["x"], position["y"]))

    return card


def create_photo_card(
    photo_paths: Iterable[str],
    output_path: str,
) -> str:
    first_three = tuple(photo_paths)[:3]
    if len(first_three) != 3:
        raise ValueError("Exactly 3 photos are required for a PhotoCard")

    card = _build_photo_card(first_three)
    final_canvas = Image.new("RGBA", (card.width * 2, card.height))
    final_canvas.paste(card, (0, 0))
    final_canvas.paste(card, (card.width, 0))

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    final_canvas.convert("RGB").save(output, quality=95, subsampling=0)
    return str(output)


def create_strip(photo_paths: Iterable[str], output_path: str) -> str:
    """Backward-compatible alias for callers using the former function name."""
    return create_photo_card(photo_paths, output_path)
