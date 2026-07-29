from __future__ import annotations

import gzip
import html
import os
from typing import BinaryIO


def mm2px(mm: float, dpi: int) -> float:
    return (mm * dpi) / 25.4


def pt2mm(pt: float) -> float:
    return pt * 0.352777778


class BaseWriter:
    def __init__(self, initialize=None, paint_module=None, paint_text=None, finish=None):
        self.module_width = 10
        self.module_height = 10
        self.font_size = 10
        self.quiet_zone = 6.5
        self.background = "white"
        self.foreground = "black"
        self.text = ""
        self.human = ""
        self.text_distance = 5
        self.text_line_distance = 1
        self.center_text = True
        self.guard_height_factor = 1.1
        self.margin_top = 1
        self.margin_bottom = 1

    def set_options(self, options: dict) -> None:
        for key, value in options.items():
            key = key.lstrip("_")
            if hasattr(self, key):
                setattr(self, key, value)

    def calculate_size(self, modules_per_line: int, number_of_lines: int) -> tuple:
        width = 2 * self.quiet_zone + modules_per_line * self.module_width
        height = self.margin_bottom + self.margin_top + (
            self.module_height * number_of_lines
        )
        lines = len(self.text.splitlines())
        if self.font_size and self.text:
            height += pt2mm(self.font_size) / 2 * lines + self.text_distance
            height += self.text_line_distance * (lines - 1)
        return width, height

    def packed(self, line: str):
        line += " "
        count = 1
        for i in range(len(line) - 1):
            if line[i] == line[i + 1]:
                count += 1
            else:
                if line[i] == "1":
                    yield count, 1.0
                elif line[i] == "G":
                    yield count, self.guard_height_factor
                else:
                    yield -count, self.guard_height_factor
                count = 1

    def save(self, filename: str, output) -> str:
        raise NotImplementedError

    def write(self, content, fp: BinaryIO) -> None:
        raise NotImplementedError


class SVGWriter(BaseWriter):
    def __init__(self) -> None:
        super().__init__()
        self.compress = False
        self.with_doctype = True

    def render(self, code: list[str]) -> bytes:
        if len(code) != 1:
            raise NotImplementedError("Only one line of code is supported")
        line = code[0]
        width, height = self.calculate_size(len(line), 1)
        parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            (
                f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" '
                f'width="{width:.3f}mm" height="{height:.3f}mm">'
            ),
            '<g id="barcode_group">',
        ]
        if self.background is not None:
            parts.append(
                f'<rect width="100%" height="100%" style="fill:{self.background}"/>'
            )
        xpos = self.quiet_zone
        ypos = self.margin_top
        for modules, factor in self.packed(line):
            run_width = self.module_width * abs(modules)
            if modules > 0:
                parts.append(
                    f'<rect x="{xpos:.3f}mm" y="{ypos:.3f}mm" '
                    f'width="{run_width:.3f}mm" '
                    f'height="{self.module_height * factor:.3f}mm" '
                    f'style="fill:{self.foreground};"/>'
                )
            xpos += run_width
        if self.text:
            xtext = self.quiet_zone + len(line) * self.module_width / 2
            ytext = self.margin_top + self.module_height + self.text_distance
            parts.append(
                f'<text x="{xtext:.3f}mm" y="{ytext:.3f}mm" '
                f'style="fill:{self.foreground};font-size:{self.font_size}pt;'
                f'text-anchor:middle">{html.escape(self.human or self.text)}</text>'
            )
        parts.extend(["</g>", "</svg>"])
        separator = "" if self.compress else os.linesep
        return separator.join(parts).encode("utf-8")

    def save(self, filename: str, output: bytes) -> str:
        if self.compress:
            full = f"{filename}.svgz"
            with gzip.open(full, "wb") as stream:
                stream.write(output)
        else:
            full = f"{filename}.svg"
            with open(full, "wb") as stream:
                stream.write(output)
        return full

    def write(self, content: bytes, fp: BinaryIO) -> None:
        fp.write(content)


ImageWriter = None
