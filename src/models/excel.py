"""Excel-related data models."""

from enum import Enum

from pydantic import BaseModel, Field, validator


class BorderStyle(str, Enum):
    """Excel border styles."""

    NONE = "none"
    THIN = "thin"
    MEDIUM = "medium"
    THICK = "thick"
    DOUBLE = "double"
    DASHED = "dashed"
    DOTTED = "dotted"
    HAIR = "hair"
    MEDIUM_DASHED = "mediumDashed"
    DASH_DOT = "dashDot"
    MEDIUM_DASH_DOT = "mediumDashDot"
    DASH_DOT_DOT = "dashDotDot"
    MEDIUM_DASH_DOT_DOT = "mediumDashDotDot"
    SLANT_DASH_DOT = "slantDashDot"


class HorizontalAlignment(str, Enum):
    """Excel horizontal alignment options."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"
    FILL = "fill"
    DISTRIBUTED = "distributed"
    CENTER_CONTINUOUS = "centerContinuous"


class VerticalAlignment(str, Enum):
    """Excel vertical alignment options."""

    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"
    JUSTIFY = "justify"
    DISTRIBUTED = "distributed"


class ExcelColor(BaseModel):
    """Represents an Excel color."""

    rgb: str | None = None  # Hex color like "FF0000"
    theme: int | None = None  # Theme color index
    tint: float | None = None  # Tint value (-1 to 1)

    @validator("rgb")
    def validate_rgb(cls, v):
        """Validate RGB color format."""
        if v and not (len(v) == 6 and all(c in "0123456789ABCDEFabcdef" for c in v)):
            raise ValueError("RGB must be a 6-character hex string")
        return v.upper() if v else v

    @validator("tint")
    def validate_tint(cls, v):
        """Validate tint value."""
        if v is not None and not -1 <= v <= 1:
            raise ValueError("Tint must be between -1 and 1")
        return v


class ExcelFont(BaseModel):
    """Represents Excel font settings."""

    name: str = "Calibri"
    size: int = 11
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    color: ExcelColor | None = None


class ExcelBorder(BaseModel):
    """Represents Excel border settings."""

    left: BorderStyle | None = None
    right: BorderStyle | None = None
    top: BorderStyle | None = None
    bottom: BorderStyle | None = None
    diagonal: BorderStyle | None = None
    diagonal_up: bool = False
    diagonal_down: bool = False
    color: ExcelColor | None = None


class ExcelFill(BaseModel):
    """Represents Excel fill settings."""

    pattern_type: str = "solid"
    fg_color: ExcelColor | None = None
    bg_color: ExcelColor | None = None


class ExcelAlignment(BaseModel):
    """Represents Excel alignment settings."""

    horizontal: HorizontalAlignment = HorizontalAlignment.LEFT
    vertical: VerticalAlignment = VerticalAlignment.BOTTOM
    text_rotation: int = 0
    wrap_text: bool = False
    shrink_to_fit: bool = False
    indent: int = 0

    @validator("text_rotation")
    def validate_rotation(cls, v):
        """Validate text rotation angle."""
        if not -90 <= v <= 90 and v != 255:  # 255 is vertical text
            raise ValueError("Text rotation must be between -90 and 90 or 255")
        return v


class ExcelStyle(BaseModel):
    """Represents complete Excel cell style."""

    font: ExcelFont | None = None
    border: ExcelBorder | None = None
    fill: ExcelFill | None = None
    alignment: ExcelAlignment | None = None
    number_format: str = "General"
    protection_locked: bool = True
    protection_hidden: bool = False


class ExcelRange(BaseModel):
    """Represents an Excel range."""

    sheet_name: str
    start_row: int = Field(ge=1)
    start_col: int = Field(ge=1)
    end_row: int = Field(ge=1)
    end_col: int = Field(ge=1)

    @validator("end_row")
    def validate_end_row(cls, v, values):
        """Validate end row is not before start row."""
        if "start_row" in values and v < values["start_row"]:
            raise ValueError("End row cannot be before start row")
        return v

    @validator("end_col")
    def validate_end_col(cls, v, values):
        """Validate end column is not before start column."""
        if "start_col" in values and v < values["start_col"]:
            raise ValueError("End column cannot be before start column")
        return v

    def to_excel_range(self) -> str:
        """Convert to Excel range notation (e.g., 'A1:C10').

        Returns:
            Excel range string.
        """
        start_col_letter = self._col_to_letter(self.start_col)
        end_col_letter = self._col_to_letter(self.end_col)
        return f"{start_col_letter}{self.start_row}:{end_col_letter}{self.end_row}"

    @staticmethod
    def _col_to_letter(col_num: int) -> str:
        """Convert column number to Excel letter.

        Args:
            col_num: Column number (1-based).

        Returns:
            Excel column letter(s).
        """
        result = ""
        while col_num > 0:
            col_num -= 1
            result = chr(65 + col_num % 26) + result
            col_num //= 26
        return result

    @staticmethod
    def from_excel_range(sheet_name: str, range_str: str) -> "ExcelRange":
        """Create from Excel range notation.

        Args:
            sheet_name: Name of the worksheet.
            range_str: Excel range string (e.g., 'A1:C10').

        Returns:
            ExcelRange instance.
        """
        import re

        pattern = r"([A-Z]+)(\d+):([A-Z]+)(\d+)"
        match = re.match(pattern, range_str.upper())

        if not match:
            raise ValueError(f"Invalid Excel range: {range_str}")

        start_col_letter, start_row, end_col_letter, end_row = match.groups()

        return ExcelRange(
            sheet_name=sheet_name,
            start_row=int(start_row),
            start_col=ExcelRange._letter_to_col(start_col_letter),
            end_row=int(end_row),
            end_col=ExcelRange._letter_to_col(end_col_letter),
        )

    @staticmethod
    def _letter_to_col(col_letter: str) -> int:
        """Convert Excel column letter to number.

        Args:
            col_letter: Excel column letter(s).

        Returns:
            Column number (1-based).
        """
        result = 0
        for char in col_letter:
            result = result * 26 + (ord(char) - ord("A") + 1)
        return result


class ExcelWorksheet(BaseModel):
    """Represents an Excel worksheet."""

    name: str
    tab_color: ExcelColor | None = None
    hidden: bool = False
    zoom: int = 100
    freeze_panes: tuple[int, int] | None = None  # (row, col)
    auto_filter: ExcelRange | None = None
    print_area: ExcelRange | None = None
    row_heights: dict[int, float] = Field(default_factory=dict)
    column_widths: dict[int, float] = Field(default_factory=dict)

    @validator("name")
    def validate_name(cls, v):
        """Validate worksheet name."""
        invalid_chars = [":", "\\", "/", "?", "*", "[", "]"]
        if any(char in v for char in invalid_chars):
            raise ValueError(f"Worksheet name cannot contain: {', '.join(invalid_chars)}")
        if len(v) > 31:
            raise ValueError("Worksheet name cannot exceed 31 characters")
        return v

    @validator("zoom")
    def validate_zoom(cls, v):
        """Validate zoom level."""
        if not 10 <= v <= 400:
            raise ValueError("Zoom must be between 10 and 400")
        return v


class ExcelFormula(BaseModel):
    """Represents an Excel formula."""

    formula: str
    is_array: bool = False
    range: ExcelRange | None = None

    @validator("formula")
    def validate_formula(cls, v):
        """Validate formula starts with =."""
        if not v.startswith("="):
            v = "=" + v
        return v


class ExcelValidation(BaseModel):
    """Represents Excel data validation."""

    type: str  # "list", "whole", "decimal", "date", "time", "textLength", "custom"
    operator: str = "between"  # "between", "notBetween", "equal", "notEqual", "greaterThan", etc.
    formula1: str | None = None
    formula2: str | None = None
    list_values: list[str] | None = None
    show_dropdown: bool = True
    show_input_message: bool = False
    input_title: str | None = None
    input_message: str | None = None
    show_error_message: bool = True
    error_style: str = "stop"  # "stop", "warning", "information"
    error_title: str | None = None
    error_message: str | None = None
