"""Vision Engine for screen analysis and UI detection."""
import base64
import io
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from loguru import logger
from PIL import Image, ImageDraw, ImageFont

from config import settings


@dataclass
class UIElement:
    """Represents a detected UI element."""
    element_type: str
    x: int
    y: int
    width: int
    height: int
    confidence: float
    text: Optional[str] = None
    attributes: Dict[str, Any] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}

    @property
    def center(self) -> Tuple[int, int]:
        """Get center coordinates."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Get bounding box."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "element_type": self.element_type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence,
            "text": self.text,
            "attributes": self.attributes,
            "center": self.center,
        }


class VisionEngine:
    """Computer vision engine for screen analysis."""

    # UI element detection templates
    ELEMENT_TYPES = [
        "button", "text_field", "checkbox", "radio", "dropdown",
        "menu", "dialog", "notification", "tab", "link", "icon",
        "image", "table", "list", "scrollbar", "window", "title_bar"
    ]

    def __init__(self):
        self.screenshot_count = 0
        self.last_screenshot: Optional[np.ndarray] = None
        self.last_screenshot_path: Optional[str] = None
        logger.info("VisionEngine initialized")

    def capture_screenshot(self, save: bool = True) -> Tuple[np.ndarray, Optional[str]]:
        """Capture a screenshot of the current screen."""
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            self.last_screenshot = img

            path = None
            if save:
                self.screenshot_count += 1
                timestamp = int(time.time() * 1000)
                filename = f"screenshot_{timestamp}_{self.screenshot_count}.png"
                path = str(settings.screenshot_path / filename)
                cv2.imwrite(path, img)
                self.last_screenshot_path = path
                logger.debug(f"Screenshot saved: {path}")

            return img, path
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            # Return blank image as fallback
            return np.zeros((1080, 1920, 3), dtype=np.uint8), None

    def analyze_image(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze an image and extract comprehensive information."""
        height, width = image.shape[:2]

        analysis = {
            "dimensions": {"width": width, "height": height},
            "elements": [],
            "layout": {},
            "colors": {},
            "text_regions": [],
            "interactive_elements": [],
        }

        # Detect UI elements
        elements = self.detect_ui_elements(image)
        analysis["elements"] = [e.to_dict() for e in elements]

        # Detect layout
        analysis["layout"] = self.detect_layout(image)

        # Detect color scheme
        analysis["colors"] = self.analyze_colors(image)

        # Find text regions
        analysis["text_regions"] = self.detect_text_regions(image)

        # Find interactive elements
        analysis["interactive_elements"] = [
            e.to_dict() for e in elements 
            if e.element_type in ["button", "text_field", "checkbox", "radio", "dropdown", "link", "tab"]
        ]

        return analysis

    def detect_ui_elements(self, image: np.ndarray) -> List[UIElement]:
        """Detect UI elements in the image."""
        elements = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect buttons (rectangular shapes with text)
        buttons = self._detect_buttons(image, gray)
        elements.extend(buttons)

        # Detect text fields (rectangular input areas)
        text_fields = self._detect_text_fields(image, gray)
        elements.extend(text_fields)

        # Detect checkboxes and radio buttons
        checkboxes = self._detect_checkboxes(gray)
        elements.extend(checkboxes)

        # Detect dropdowns
        dropdowns = self._detect_dropdowns(image, gray)
        elements.extend(dropdowns)

        # Detect menus and tabs
        menus = self._detect_menus(image, gray)
        elements.extend(menus)

        # Detect links
        links = self._detect_links(image, gray)
        elements.extend(links)

        # Detect icons
        icons = self._detect_icons(gray)
        elements.extend(icons)

        # Detect windows and dialogs
        windows = self._detect_windows(gray)
        elements.extend(windows)

        # Sort by position (top to bottom, left to right)
        elements.sort(key=lambda e: (e.y, e.x))

        return elements

    def _detect_buttons(self, image: np.ndarray, gray: np.ndarray) -> List[UIElement]:
        """Detect button elements."""
        elements = []

        # Use contour detection for buttons
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h) if h > 0 else 0
            area = w * h

            # Button heuristics
            if 20 < w < 400 and 15 < h < 100 and 1.5 < aspect_ratio < 8 and area > 300:
                # Check if it looks like a button (has border or different background)
                roi = image[y:y+h, x:x+w]
                if self._is_button_like(roi):
                    elements.append(UIElement(
                        element_type="button",
                        x=x, y=y, width=w, height=h,
                        confidence=0.75,
                        text=None,
                    ))

        return elements

    def _detect_text_fields(self, image: np.ndarray, gray: np.ndarray) -> List[UIElement]:
        """Detect text input fields."""
        elements = []

        # Look for rectangular regions with light backgrounds and borders
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h) if h > 0 else 0

            # Text field heuristics
            if 80 < w < 600 and 20 < h < 60 and aspect_ratio > 3:
                roi = image[y:y+h, x:x+w]
                if self._is_text_field_like(roi):
                    elements.append(UIElement(
                        element_type="text_field",
                        x=x, y=y, width=w, height=h,
                        confidence=0.7,
                        text=None,
                    ))

        return elements

    def _detect_checkboxes(self, gray: np.ndarray) -> List[UIElement]:
        """Detect checkbox and radio button elements."""
        elements = []

        # Look for small square or circular shapes
        _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            if 10 < w < 30 and 10 < h < 30:
                aspect_ratio = w / float(h) if h > 0 else 0
                if 0.8 < aspect_ratio < 1.2:
                    # Square - likely checkbox
                    elements.append(UIElement(
                        element_type="checkbox",
                        x=x, y=y, width=w, height=h,
                        confidence=0.65,
                    ))
                elif 0.7 < aspect_ratio < 1.3:
                    # Could be radio button (circular)
                    elements.append(UIElement(
                        element_type="radio",
                        x=x, y=y, width=w, height=h,
                        confidence=0.6,
                    ))

        return elements

    def _detect_dropdowns(self, image: np.ndarray, gray: np.ndarray) -> List[UIElement]:
        """Detect dropdown/select elements."""
        elements = []

        # Dropdowns usually have a downward arrow or chevron
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h) if h > 0 else 0

            if 80 < w < 400 and 25 < h < 60 and aspect_ratio > 2:
                # Check for dropdown arrow indicator
                roi = image[y:y+h, x:x+w]
                if self._has_dropdown_indicator(roi):
                    elements.append(UIElement(
                        element_type="dropdown",
                        x=x, y=y, width=w, height=h,
                        confidence=0.7,
                    ))

        return elements

    def _detect_menus(self, image: np.ndarray, gray: np.ndarray) -> List[UIElement]:
        """Detect menu and tab elements."""
        elements = []

        # Menu bars are typically at the top with horizontal layout
        height, width = image.shape[:2]

        # Check top portion for menu bar
        top_region = gray[:100, :]
        edges = cv2.Canny(top_region, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            if 40 < w < 200 and 20 < h < 50 and x < width - 50:
                elements.append(UIElement(
                    element_type="menu" if y < 50 else "tab",
                    x=x, y=y, width=w, height=h,
                    confidence=0.6,
                ))

        return elements

    def _detect_links(self, image: np.ndarray, gray: np.ndarray) -> List[UIElement]:
        """Detect hyperlink elements."""
        elements = []

        # Links are typically blue and underlined
        # This is a simplified detection - in production, use OCR + color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Blue color range for links
        lower_blue = np.array([100, 50, 50])
        upper_blue = np.array([130, 255, 255])
        mask = cv2.inRange(hsv, lower_blue, upper_blue)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 30 and h > 10 and w / float(h) > 2:
                elements.append(UIElement(
                    element_type="link",
                    x=x, y=y, width=w, height=h,
                    confidence=0.5,
                ))

        return elements

    def _detect_icons(self, gray: np.ndarray) -> List[UIElement]:
        """Detect icon elements."""
        elements = []

        # Icons are small square images
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h) if h > 0 else 0

            if 16 < w < 64 and 16 < h < 64 and 0.7 < aspect_ratio < 1.3:
                elements.append(UIElement(
                    element_type="icon",
                    x=x, y=y, width=w, height=h,
                    confidence=0.55,
                ))

        return elements

    def _detect_windows(self, gray: np.ndarray) -> List[UIElement]:
        """Detect window and dialog boundaries."""
        elements = []

        # Look for large rectangular regions with borders
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        height, width = gray.shape

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Window heuristics - large rectangles
            if w > width * 0.3 and h > height * 0.3 and w < width * 0.95 and h < height * 0.95:
                elements.append(UIElement(
                    element_type="window",
                    x=x, y=y, width=w, height=h,
                    confidence=0.6,
                ))
            elif w > 200 and h > 150 and w < width * 0.8 and h < height * 0.8:
                elements.append(UIElement(
                    element_type="dialog",
                    x=x, y=y, width=w, height=h,
                    confidence=0.55,
                ))

        return elements

    def detect_text_regions(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect regions containing text."""
        regions = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Use MSER for text region detection
        mser = cv2.MSER_create()
        regions_mser, _ = mser.detectRegions(gray)

        for region in regions_mser:
            x, y, w, h = cv2.boundingRect(region.reshape(-1, 1, 2))
            if w > 20 and h > 10 and w / float(h) > 1.5:
                regions.append({
                    "x": x, "y": y, "width": w, "height": h,
                    "area": w * h,
                })

        return regions

    def detect_layout(self, image: np.ndarray) -> Dict[str, Any]:
        """Detect page/application layout structure."""
        height, width = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        layout = {
            "screen_size": {"width": width, "height": height},
            "header_region": None,
            "sidebar_region": None,
            "main_content_region": None,
            "footer_region": None,
        }

        # Detect header (top 10-15%)
        header_roi = gray[:int(height*0.15), :]
        if np.mean(header_roi) < 250:  # Not completely white
            layout["header_region"] = {"x": 0, "y": 0, "width": width, "height": int(height*0.15)}

        # Detect sidebar (left 15-25%)
        sidebar_roi = gray[:, :int(width*0.25)]
        if np.mean(sidebar_roi) < 250:
            layout["sidebar_region"] = {"x": 0, "y": 0, "width": int(width*0.25), "height": height}

        # Main content area
        main_x = int(width * 0.25) if layout["sidebar_region"] else 0
        main_y = int(height * 0.15) if layout["header_region"] else 0
        layout["main_content_region"] = {
            "x": main_x, "y": main_y,
            "width": width - main_x,
            "height": height - main_y,
        }

        return layout

    def analyze_colors(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze color scheme of the image."""
        # Calculate dominant colors
        pixels = image.reshape(-1, 3).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, 5, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        colors = []
        for center in centers:
            b, g, r = center.astype(int)
            colors.append({
                "rgb": [int(r), int(g), int(b)],
                "hex": f"#{r:02x}{g:02x}{b:02x}",
            })

        return {
            "dominant_colors": colors,
            "is_dark_mode": np.mean(gray := cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)) < 128,
        }

    def _is_button_like(self, roi: np.ndarray) -> bool:
        """Check if ROI looks like a button."""
        # Buttons typically have rounded corners or distinct borders
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        std = np.std(gray)
        return std > 10  # Has some variation (not flat)

    def _is_text_field_like(self, roi: np.ndarray) -> bool:
        """Check if ROI looks like a text field."""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        # Text fields usually have light background
        mean = np.mean(gray)
        return 200 < mean < 250

    def _has_dropdown_indicator(self, roi: np.ndarray) -> bool:
        """Check if ROI has a dropdown arrow indicator."""
        # Look for small triangle or chevron shape on the right side
        height, width = roi.shape[:2]
        right_side = roi[:, int(width*0.8):]
        gray = cv2.cvtColor(right_side, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return np.sum(edges > 0) > 20

    def draw_elements(self, image: np.ndarray, elements: List[UIElement]) -> np.ndarray:
        """Draw bounding boxes around detected elements."""
        result = image.copy()

        colors = {
            "button": (0, 255, 0),
            "text_field": (255, 0, 0),
            "checkbox": (0, 255, 255),
            "radio": (255, 255, 0),
            "dropdown": (255, 0, 255),
            "menu": (128, 255, 128),
            "tab": (255, 128, 0),
            "link": (0, 128, 255),
            "icon": (128, 128, 128),
            "window": (255, 255, 255),
            "dialog": (200, 200, 200),
        }

        for element in elements:
            color = colors.get(element.element_type, (255, 255, 255))
            x1, y1, x2, y2 = element.bbox
            cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)

            label = f"{element.element_type} ({element.confidence:.2f})"
            cv2.putText(result, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        return result

    def encode_image_base64(self, image: np.ndarray, format: str = "png") -> str:
        """Encode image to base64 string."""
        _, buffer = cv2.imencode(f".{format}", image)
        return base64.b64encode(buffer).decode("utf-8")

    def decode_image_base64(self, base64_string: str) -> np.ndarray:
        """Decode base64 string to image."""
        buffer = base64.b64decode(base64_string)
        nparr = np.frombuffer(buffer, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    def find_element_by_text(self, image: np.ndarray, text: str) -> Optional[UIElement]:
        """Find an element containing specific text."""
        elements = self.detect_ui_elements(image)

        for element in elements:
            if element.text and text.lower() in element.text.lower():
                return element

        return None

    def find_element_by_type(self, image: np.ndarray, element_type: str) -> List[UIElement]:
        """Find all elements of a specific type."""
        elements = self.detect_ui_elements(image)
        return [e for e in elements if e.element_type == element_type]

    def get_element_at_position(self, image: np.ndarray, x: int, y: int) -> Optional[UIElement]:
        """Get the element at a specific position."""
        elements = self.detect_ui_elements(image)

        for element in elements:
            x1, y1, x2, y2 = element.bbox
            if x1 <= x <= x2 and y1 <= y <= y2:
                return element

        return None

    def compare_screenshots(self, img1: np.ndarray, img2: np.ndarray) -> Dict[str, Any]:
        """Compare two screenshots and find differences."""
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        diff = cv2.absdiff(img1, img2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        changes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 10 and h > 10:
                changes.append({"x": x, "y": y, "width": w, "height": h})

        total_pixels = img1.shape[0] * img1.shape[1]
        changed_pixels = np.sum(thresh > 0)

        return {
            "similarity": 1.0 - (changed_pixels / total_pixels),
            "changes": changes,
            "change_count": len(changes),
            "significant_change": len(changes) > 5 or (changed_pixels / total_pixels) > 0.01,
        }


# Global vision engine instance
vision_engine = VisionEngine()
