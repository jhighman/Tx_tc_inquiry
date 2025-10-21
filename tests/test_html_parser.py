"""
Tests for HTML-based parser module.
"""

import pytest
from unittest.mock import Mock, patch

from arrestx.config import Config
from arrestx.html_parser import (
    parse_html_content,
    _parse_text_line_to_row,
    _normalize_name,
    _normalize_date,
    _text_to_html_table,
    _is_header_or_footer,
)

# Skip tests if BeautifulSoup is not available
pytest.importorskip("bs4")


class TestHTMLParser:
    """Test HTML parser functionality."""

    def test_parse_html_table_basic(self):
        """Test parsing a basic HTML table."""
        html_content = """
        <html>
        <body>
        <table>
            <tr>
                <th>Inmate Name</th>
                <th>Identifier CID</th>
                <th>Book In Date</th>
                <th>Booking No.</th>
                <th>Description</th>
            </tr>
            <tr>
                <td>SMITH, JOHN DOE</td>
                <td>1234567</td>
                <td>10/20/2025</td>
                <td>25-0241234</td>
                <td>ASSAULT FAMILY VIOLENCE</td>
            </tr>
            <tr>
                <td>JONES, JANE MARIE</td>
                <td>7654321</td>
                <td>10/21/2025</td>
                <td>25-0241235</td>
                <td>DRIVING WHILE INTOXICATED</td>
            </tr>
        </table>
        </body>
        </html>
        """
        
        cfg = Config()
        records = parse_html_content(html_content, "test.pdf", cfg)
        
        assert len(records) == 2
        
        # Check first record
        assert records[0]["name"] == "SMITH, JOHN DOE"
        assert records[0]["name_normalized"] == "John Doe Smith"
        assert records[0]["identifier"] == "1234567"
        assert records[0]["book_in_date"] == "2025-10-20"
        assert len(records[0]["charges"]) == 1
        assert records[0]["charges"][0]["booking_no"] == "25-0241234"
        assert records[0]["charges"][0]["description"] == "ASSAULT FAMILY VIOLENCE"
        
        # Check second record
        assert records[1]["name"] == "JONES, JANE MARIE"
        assert records[1]["name_normalized"] == "Jane Marie Jones"
        assert records[1]["identifier"] == "7654321"
        assert records[1]["book_in_date"] == "2025-10-21"
        assert len(records[1]["charges"]) == 1
        assert records[1]["charges"][0]["booking_no"] == "25-0241235"
        assert records[1]["charges"][0]["description"] == "DRIVING WHILE INTOXICATED"

    def test_parse_text_line_to_row(self):
        """Test parsing text lines into row data."""
        # Test name extraction
        row = _parse_text_line_to_row("SMITH, JOHN DOE 1234567 10/20/2025 25-0241234 ASSAULT")
        assert row["name"] == "SMITH, JOHN DOE"
        assert row["identifier"] == "1234567"
        assert row["date"] == "10/20/2025"
        assert row["booking"] == "25-0241234"
        assert row["description"] == "ASSAULT"
        
        # Test partial data
        row = _parse_text_line_to_row("1234567 10/20/2025")
        assert row["identifier"] == "1234567"
        assert row["date"] == "10/20/2025"
        assert "name" not in row

    def test_normalize_name(self):
        """Test name normalization."""
        assert _normalize_name("SMITH, JOHN DOE") == "John Doe Smith"
        assert _normalize_name("JONES, JANE") == "Jane Jones"
        assert _normalize_name("INVALID") == "INVALID"
        assert _normalize_name("") == ""

    def test_normalize_date(self):
        """Test date normalization."""
        assert _normalize_date("10/20/2025") == "2025-10-20"
        assert _normalize_date("1/5/2025") == "2025-01-05"
        assert _normalize_date("invalid") == "invalid"
        assert _normalize_date(None) is None

    def test_text_to_html_table(self):
        """Test converting text to HTML table."""
        text = """
        Daily Booked In Report
        Inmate Name    Identifier CID    Book In Date    Booking No.    Description
        SMITH, JOHN DOE    1234567    10/20/2025    25-0241234    ASSAULT
        JONES, JANE    7654321    10/21/2025    25-0241235    DWI
        """
        
        html_table = _text_to_html_table(text, 1)
        assert html_table is not None
        assert "<table" in html_table
        assert "SMITH, JOHN DOE" in html_table
        assert "JONES, JANE" in html_table

    def test_is_header_or_footer(self):
        """Test header/footer detection."""
        assert _is_header_or_footer("Daily Booked In Report")
        assert _is_header_or_footer("Page: 1 of 5")
        assert _is_header_or_footer("Report Date: 10/20/2025")
        assert _is_header_or_footer("---------------------")
        assert not _is_header_or_footer("SMITH, JOHN DOE")
        assert not _is_header_or_footer("25-0241234 ASSAULT")

    def test_html_table_with_continuation_rows(self):
        """Test parsing HTML table with continuation rows."""
        html_content = """
        <html>
        <body>
        <table>
            <tr>
                <th>Inmate Name</th>
                <th>Identifier CID</th>
                <th>Book In Date</th>
                <th>Booking No.</th>
                <th>Description</th>
            </tr>
            <tr>
                <td>SMITH, JOHN DOE</td>
                <td>1234567</td>
                <td>10/20/2025</td>
                <td>25-0241234</td>
                <td>ASSAULT FAMILY VIOLENCE</td>
            </tr>
            <tr>
                <td colspan="5">BODILY INJURY FAMILY MEMBER</td>
            </tr>
            <tr>
                <td></td>
                <td></td>
                <td></td>
                <td>25-0241235</td>
                <td>DRIVING WHILE INTOXICATED</td>
            </tr>
        </table>
        </body>
        </html>
        """
        
        cfg = Config()
        records = parse_html_content(html_content, "test.pdf", cfg)
        
        assert len(records) == 1
        assert records[0]["name"] == "SMITH, JOHN DOE"
        assert len(records[0]["charges"]) == 2
        assert records[0]["charges"][0]["description"] == "ASSAULT FAMILY VIOLENCE BODILY INJURY FAMILY MEMBER"
        assert records[0]["charges"][1]["booking_no"] == "25-0241235"
        assert records[0]["charges"][1]["description"] == "DRIVING WHILE INTOXICATED"

    @patch('arrestx.html_parser.convert_pdf_to_html')
    def test_parse_pdf_via_html_success(self, mock_convert):
        """Test successful PDF to HTML parsing."""
        from arrestx.html_parser import parse_pdf_via_html
        
        mock_convert.return_value = """
        <html>
        <body>
        <table>
            <tr>
                <th>Inmate Name</th>
                <th>Identifier CID</th>
                <th>Book In Date</th>
                <th>Booking No.</th>
                <th>Description</th>
            </tr>
            <tr>
                <td>SMITH, JOHN</td>
                <td>1234567</td>
                <td>10/20/2025</td>
                <td>25-0241234</td>
                <td>ASSAULT</td>
            </tr>
        </table>
        </body>
        </html>
        """
        
        cfg = Config()
        records = parse_pdf_via_html("test.pdf", cfg)
        
        assert len(records) == 1
        assert records[0]["name"] == "SMITH, JOHN"
        mock_convert.assert_called_once_with("test.pdf", cfg)

    @patch('arrestx.html_parser.convert_pdf_to_html')
    def test_parse_pdf_via_html_failure(self, mock_convert):
        """Test PDF to HTML parsing failure."""
        from arrestx.html_parser import parse_pdf_via_html
        
        mock_convert.return_value = None
        
        cfg = Config()
        
        with pytest.raises(RuntimeError, match="Failed to convert PDF to HTML"):
            parse_pdf_via_html("test.pdf", cfg)

    def test_empty_html_table(self):
        """Test parsing empty HTML table."""
        html_content = """
        <html>
        <body>
        <table>
            <tr>
                <th>Inmate Name</th>
                <th>Identifier CID</th>
                <th>Book In Date</th>
                <th>Booking No.</th>
                <th>Description</th>
            </tr>
        </table>
        </body>
        </html>
        """
        
        cfg = Config()
        records = parse_html_content(html_content, "test.pdf", cfg)
        
        assert len(records) == 0

    def test_malformed_html(self):
        """Test parsing malformed HTML."""
        html_content = """
        <html>
        <body>
        <table>
            <tr>
                <td>SMITH, JOHN</td>
                <td>1234567</td>
                <!-- Missing closing tags -->
        """
        
        cfg = Config()
        # Should not raise an exception, BeautifulSoup handles malformed HTML
        records = parse_html_content(html_content, "test.pdf", cfg)
        
        # May or may not parse correctly, but shouldn't crash
        assert isinstance(records, list)