from __future__ import annotations

from .writer import SVGWriter


class Barcode:
    name = ""
    digits = 0
    default_writer = SVGWriter
    default_writer_options = {
        "module_width": 0.2,
        "module_height": 15.0,
        "quiet_zone": 6.5,
        "font_size": 10,
        "text_distance": 5.0,
        "background": "white",
        "foreground": "black",
        "write_text": True,
        "text": "",
    }

    def to_ascii(self) -> str:
        code = self.build()
        if len(code) != 1:
            raise RuntimeError("Code list must contain a single element.")
        return code[0].replace("1", "X").replace("0", " ")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.get_fullcode()!r})>"

    def save(
        self, filename: str, options: dict | None = None, text: str | None = None
    ) -> str:
        rendered = self.render(options, text)
        return self.writer.save(filename, rendered)

    def write(self, fp, options: dict | None = None, text: str | None = None) -> None:
        self.writer.write(self.render(options, text), fp)

    def render(self, writer_options: dict | None = None, text: str | None = None):
        options = self.default_writer_options.copy()
        options.update(writer_options or {})
        if options.pop("write_text", True) or text is not None:
            options["text"] = self.get_fullcode() if text is None else text
        self.writer.set_options(options)
        return self.writer.render(self.build())
