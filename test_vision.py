"""Tests for Vision Engine."""
import pytest
import numpy as np
from agents.vision.vision import VisionEngine, UIElement


class TestVisionEngine:
    """Test suite for VisionEngine."""

    @pytest.fixture
    def vision(self):
        return VisionEngine()

    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        return np.zeros((1080, 1920, 3), dtype=np.uint8)

    def test_capture_screenshot(self, vision):
        """Test screenshot capture."""
        img, path = vision.capture_screenshot(save=False)
        assert img is not None
        assert isinstance(img, np.ndarray)
        assert len(img.shape) == 3

    def test_analyze_image(self, vision, sample_image):
        """Test image analysis."""
        analysis = vision.analyze_image(sample_image)
        assert "dimensions" in analysis
        assert "elements" in analysis
        assert "layout" in analysis
        assert "colors" in analysis

    def test_detect_ui_elements(self, vision, sample_image):
        """Test UI element detection."""
        elements = vision.detect_ui_elements(sample_image)
        assert isinstance(elements, list)
        for element in elements:
            assert isinstance(element, UIElement)
            assert element.element_type in vision.ELEMENT_TYPES

    def test_ui_element_properties(self):
        """Test UIElement dataclass."""
        element = UIElement(
            element_type="button",
            x=100,
            y=200,
            width=50,
            height=30,
            confidence=0.85,
        )
        assert element.center == (125, 215)
        assert element.bbox == (100, 200, 150, 230)
        assert element.to_dict()["element_type"] == "button"

    def test_encode_decode_base64(self, vision, sample_image):
        """Test base64 encoding/decoding."""
        encoded = vision.encode_image_base64(sample_image)
        assert isinstance(encoded, str)
        assert len(encoded) > 0

        decoded = vision.decode_image_base64(encoded)
        assert decoded.shape == sample_image.shape

    def test_compare_screenshots(self, vision, sample_image):
        """Test screenshot comparison."""
        img2 = sample_image.copy()
        result = vision.compare_screenshots(sample_image, img2)
        assert "similarity" in result
        assert "changes" in result
        assert result["similarity"] > 0.99

    def test_find_element_by_type(self, vision, sample_image):
        """Test finding elements by type."""
        elements = vision.find_element_by_type(sample_image, "button")
        assert isinstance(elements, list)


class TestVisionIntegration:
    """Integration tests for Vision Engine."""

    def test_full_pipeline(self):
        """Test full vision pipeline."""
        vision = VisionEngine()
        img, _ = vision.capture_screenshot(save=False)

        # Analyze
        analysis = vision.analyze_image(img)
        assert analysis["dimensions"]["width"] > 0
        assert analysis["dimensions"]["height"] > 0

        # Detect elements
        elements = analysis["elements"]
        assert isinstance(elements, list)

        # Draw elements
        drawn = vision.draw_elements(img, [UIElement(
            element_type="button", x=100, y=100, width=50, height=30, confidence=0.9
        )])
        assert drawn.shape == img.shape
