"""Tests for OCR Engine."""
import pytest
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from agents.ocr.ocr import OCREngine, TextRegion


class TestOCREngine:
    """Test suite for OCREngine."""

    @pytest.fixture
    def ocr(self):
        return OCREngine()

    @pytest.fixture
    def text_image(self):
        """Create an image with text for testing."""
        img = Image.new("RGB", (400, 100), color="white")
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()
        draw.text((10, 10), "Hello World Test", fill="black", font=font)
        return np.array(img)

    def test_read_text(self, ocr, text_image):
        """Test text reading."""
        regions = ocr.read_text(text_image, languages=["en"])
        assert isinstance(regions, list)
        for region in regions:
            assert isinstance(region, TextRegion)
            assert len(region.text) > 0

    def test_find_text(self, ocr, text_image):
        """Test finding specific text."""
        matches = ocr.find_text(text_image, "Hello", case_sensitive=False)
        assert isinstance(matches, list)

    def test_get_all_text(self, ocr, text_image):
        """Test getting all text."""
        text = ocr.get_all_text(text_image, languages=["en"])
        assert isinstance(text, str)
        assert len(text) > 0

    def test_get_structured_text(self, ocr, text_image):
        """Test structured text extraction."""
        structured = ocr.get_structured_text(text_image)
        assert "full_text" in structured
        assert "lines" in structured
        assert "regions" in structured

    def test_preprocess_for_ocr(self, ocr, text_image):
        """Test image preprocessing."""
        processed = ocr.preprocess_for_ocr(text_image)
        assert processed.shape[:2] == text_image.shape[:2]
        assert len(processed.shape) == 2  # Grayscale

    def test_detect_language(self, ocr, text_image):
        """Test language detection."""
        lang = ocr.detect_language(text_image)
        assert lang in ocr.SUPPORTED_LANGUAGES

    def test_text_region_dataclass(self):
        """Test TextRegion dataclass."""
        region = TextRegion(
            text="Test",
            x=10,
            y=20,
            width=100,
            height=30,
            confidence=0.95,
        )
        assert region.to_dict()["text"] == "Test"
        assert region.to_dict()["confidence"] == 0.95


class TestOCROverlap:
    """Test overlap calculation."""

    def test_overlap_calculation(self):
        """Test region overlap calculation."""
        ocr = OCREngine()
        r1 = TextRegion("Hello", 0, 0, 100, 50, 0.9)
        r2 = TextRegion("World", 50, 0, 100, 50, 0.9)

        overlap = ocr._calculate_overlap(r1, r2)
        assert 0.0 < overlap <= 1.0

    def test_no_overlap(self):
        """Test non-overlapping regions."""
        ocr = OCREngine()
        r1 = TextRegion("Hello", 0, 0, 50, 50, 0.9)
        r2 = TextRegion("World", 200, 200, 50, 50, 0.9)

        overlap = ocr._calculate_overlap(r1, r2)
        assert overlap == 0.0
