from pathlib import Path

from PIL import Image

from config import PHOTO_CARD_TEMPLATE, PHOTO_LAYOUT
from strip import create_photo_card


def test_photo_card_uses_template_layout_and_duplicate_output(tmp_path: Path):
    photo_paths = []
    colors = ((255, 0, 0), (0, 255, 0), (0, 0, 255))

    for index, color in enumerate(colors, 1):
        photo_path = tmp_path / f"photo{index}.jpg"
        Image.new("RGB", (900, 500), color).save(photo_path)
        photo_paths.append(str(photo_path))

    output_path = tmp_path / "photocard.jpg"
    create_photo_card(photo_paths, str(output_path))

    with Image.open(output_path) as result, Image.open(PHOTO_CARD_TEMPLATE) as template:
        assert result.size == (template.width * 2, template.height)
        assert result.crop((0, 0, template.width, template.height)).tobytes() == result.crop(
            (template.width, 0, template.width * 2, template.height)
        ).tobytes()

        for index, color in enumerate(colors, 1):
            position = PHOTO_LAYOUT[f"photo{index}"]
            actual = result.getpixel((position["x"] + 265, position["y"] + 200))
            assert all(abs(channel - expected) <= 8 for channel, expected in zip(actual, color))