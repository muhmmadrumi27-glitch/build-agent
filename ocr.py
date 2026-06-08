"""OCR Engine for text recognition from screen."""
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from loguru import logger
from PIL import Image


@dataclass
class TextRegion:
    """Represents a detected text region."""
    text: str
    x: int
    y: int
    width: int
    height: int
    confidence: float
    language: str = "en"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence,
            "language": self.language,
        }


class OCREngine:
    """OCR engine supporting multiple languages."""

    SUPPORTED_LANGUAGES = {
        "en": "English",
        "ur": "Urdu",
        "ar": "Arabic",
        "hi": "Hindi",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "fr": "French",
        "de": "German",
        "es": "Spanish",
        "ru": "Russian",
    }

    def __init__(self):
        self.easyocr_reader = None
        self.tesseract_available = False
        self._init_engines()
        logger.info("OCREngine initialized")

    def _init_engines(self) -> None:
        """Initialize OCR engines."""
        # Initialize EasyOCR
        try:
            import easyocr
            self.easyocr_reader = easyocr.Reader(
                ["en", "ur", "ar", "hi"],
                gpu=False,
                verbose=False,
            )
            logger.info("EasyOCR initialized with languages: en, ur, ar, hi")
        except Exception as e:
            logger.warning(f"EasyOCR initialization failed: {e}")

        # Check Tesseract availability
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self.tesseract_available = True
            logger.info("Tesseract OCR available")
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")

    def read_text(
        self,
        image: np.ndarray,
        languages: Optional[List[str]] = None,
        use_easyocr: bool = True,
        use_tesseract: bool = True,
    ) -> List[TextRegion]:
        """Read all text from an image."""
        results = []

        if languages is None:
            languages = ["en"]

        # Try EasyOCR first
        if use_easyocr and self.easyocr_reader is not None:
            try:
                easyocr_results = self._read_with_easyocr(image, languages)
                results.extend(easyocr_results)
            except Exception as e:
                logger.error(f"EasyOCR failed: {e}")

        # Fallback to Tesseract
        if use_tesseract and self.tesseract_available and not results:
            try:
                tesseract_results = self._read_with_tesseract(image, languages)
                results.extend(tesseract_results)
            except Exception as e:
                logger.error(f"Tesseract failed: {e}")

        # Merge overlapping regions
        results = self._merge_overlapping_regions(results)

        # Sort by position
        results.sort(key=lambda r: (r.y, r.x))

        return results

    def _read_with_easyocr(
        self,
        image: np.ndarray,
        languages: List[str],
    ) -> List[TextRegion]:
        """Read text using EasyOCR."""
        results = []

        # Convert BGR to RGB for EasyOCR
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # EasyOCR returns: ([[x1,y1], [x2,y1], [x2,y2], [x1,y2]], text, confidence)
        detections = self.easyocr_reader.readtext(rgb_image)

        for detection in detections:
            bbox, text, confidence = detection

            # Calculate bounding box
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            x = int(min(x_coords))
            y = int(min(y_coords))
            width = int(max(x_coords) - x)
            height = int(max(y_coords) - y)

            results.append(TextRegion(
                text=text.strip(),
                x=x,
                y=y,
                width=width,
                height=height,
                confidence=confidence,
                language=languages[0] if languages else "en",
            ))

        return results

    def _read_with_tesseract(
        self,
        image: np.ndarray,
        languages: List[str],
    ) -> List[TextRegion]:
        """Read text using Tesseract OCR."""
        import pytesseract

        results = []

        # Configure Tesseract
        lang = "+".join(languages) if languages else "eng"

        # Get detailed data
        data = pytesseract.image_to_data(
            image,
            lang=lang,
            output_type=pytesseract.Output.DICT,
        )

        n_boxes = len(data["text"])
        for i in range(n_boxes):
            text = data["text"][i].strip()
            conf = int(data["conf"][i])

            if text and conf > 30:  # Filter low confidence
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]

                results.append(TextRegion(
                    text=text,
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    confidence=conf / 100.0,
                    language=languages[0] if languages else "en",
                ))

        return results

    def _merge_overlapping_regions(self, regions: List[TextRegion], overlap_threshold: float = 0.5) -> List[TextRegion]:
        """Merge overlapping text regions."""
        if not regions:
            return regions

        merged = []
        used = set()

        for i, region1 in enumerate(regions):
            if i in used:
                continue

            # Find overlapping regions
            overlapping = [region1]
            for j, region2 in enumerate(regions[i+1:], start=i+1):
                if j in used:
                    continue

                if self._calculate_overlap(region1, region2) > overlap_threshold:
                    overlapping.append(region2)
                    used.add(j)

            # Merge overlapping regions
            if len(overlapping) > 1:
                merged_text = " ".join(r.text for r in overlapping)
                min_x = min(r.x for r in overlapping)
                min_y = min(r.y for r in overlapping)
                max_x = max(r.x + r.width for r in overlapping)
                max_y = max(r.y + r.height for r in overlapping)
                avg_conf = sum(r.confidence for r in overlapping) / len(overlapping)

                merged.append(TextRegion(
                    text=merged_text,
                    x=min_x,
                    y=min_y,
                    width=max_x - min_x,
                    height=max_y - min_y,
                    confidence=avg_conf,
                ))
            else:
                merged.append(region1)

            used.add(i)

        return merged

    def _calculate_overlap(self, r1: TextRegion, r2: TextRegion) -> float:
        """Calculate overlap ratio between two regions."""
        x1 = max(r1.x, r2.x)
        y1 = max(r1.y, r2.y)
        x2 = min(r1.x + r1.width, r2.x + r2.width)
        y2 = min(r1.y + r1.height, r2.y + r2.height)

        if x2 <= x1 or y2 <= y1:
            return 0.0

        overlap_area = (x2 - x1) * (y2 - y1)
        area1 = r1.width * r1.height
        area2 = r2.width * r2.height

        return overlap_area / min(area1, area2)

    def find_text(
        self,
        image: np.ndarray,
        search_text: str,
        case_sensitive: bool = False,
        exact_match: bool = False,
    ) -> List[TextRegion]:
        """Find specific text in an image."""
        regions = self.read_text(image)

        matches = []
        search = search_text if case_sensitive else search_text.lower()

        for region in regions:
            text = region.text if case_sensitive else region.text.lower()

            if exact_match:
                if text == search:
                    matches.append(region)
            else:
                if search in text:
                    matches.append(region)

        return matches

    def read_text_at_region(
        self,
        image: np.ndarray,
        x: int,
        y: int,
        width: int,
        height: int,
        languages: Optional[List[str]] = None,
    ) -> Optional[TextRegion]:
        """Read text from a specific region."""
        # Crop the region
        roi = image[y:y+height, x:x+width]

        if roi.size == 0:
            return None

        regions = self.read_text(roi, languages=languages)

        if regions:
            # Combine all text in the region
            combined_text = " ".join(r.text for r in regions)
            avg_conf = sum(r.confidence for r in regions) / len(regions)

            return TextRegion(
                text=combined_text,
                x=x,
                y=y,
                width=width,
                height=height,
                confidence=avg_conf,
            )

        return None

    def extract_form_fields(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Extract form field labels and values."""
        regions = self.read_text(image)

        fields = []
        for i, region in enumerate(regions):
            text = region.text.strip()

            # Look for common label patterns
            if any(text.endswith(suffix) for suffix in [":", "*", " -"]):
                # This might be a label
                field = {
                    "label": text,
                    "label_position": {"x": region.x, "y": region.y, "width": region.width, "height": region.height},
                    "value": None,
                    "value_position": None,
                }

                # Look for nearby value (usually to the right or below)
                for j, other in enumerate(regions[i+1:], start=i+1):
                    # Check if it's close by
                    x_dist = abs(other.x - region.x)
                    y_dist = abs(other.y - region.y)

                    if x_dist < 400 and y_dist < 100:
                        field["value"] = other.text
                        field["value_position"] = {"x": other.x, "y": other.y, "width": other.width, "height": other.height}
                        break

                fields.append(field)

        return fields

    def detect_language(self, image: np.ndarray) -> str:
        """Detect the dominant language in an image."""
        regions = self.read_text(image)

        if not regions:
            return "en"

        # Combine all text
        all_text = " ".join(r.text for r in regions)

        # Simple heuristics for language detection
        # Urdu detection
        if re.search(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]", all_text):
            return "ur"

        # Arabic detection
        if re.search(r"[\u0600-\u06FF\u0750-\u077F]", all_text):
            return "ar"

        # Hindi detection
        if re.search(r"[\u0900-\u097F]", all_text):
            return "hi"

        # Default to English
        return "en"

    def preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Noise reduction
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

        # Contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Binarization
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return binary

    def get_all_text(self, image: np.ndarray, languages: Optional[List[str]] = None) -> str:
        """Get all text from an image as a single string."""
        regions = self.read_text(image, languages=languages)
        return "\n".join(r.text for r in regions)

    def get_structured_text(self, image: np.ndarray) -> Dict[str, Any]:
        """Get structured text with positions and hierarchy."""
        regions = self.read_text(image)

        # Group by rows
        rows = []
        current_row = []
        last_y = None

        for region in regions:
            if last_y is None or abs(region.y - last_y) < 20:
                current_row.append(region)
            else:
                if current_row:
                    rows.append(current_row)
                current_row = [region]
            last_y = region.y

        if current_row:
            rows.append(current_row)

        structured = {
            "full_text": self.get_all_text(image),
            "lines": [],
            "regions": [r.to_dict() for r in regions],
        }

        for row in rows:
            line_text = " ".join(r.text for r in row)
            structured["lines"].append({
                "text": line_text,
                "regions": [r.to_dict() for r in row],
            })

        return structured


# Global OCR engine instance
ocr_engine = OCREngine()
