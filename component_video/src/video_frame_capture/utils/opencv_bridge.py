"""
OpenCV-Qt conversion utilities and bridge functions.
"""

from typing import Optional, Tuple
import numpy as np
import cv2
from PySide6.QtGui import QImage, QPixmap, QColor
from PySide6.QtCore import QSize
from PySide6.QtMultimedia import QVideoFrame


class OpenCVBridge:
    """Bridge for converting between Qt and OpenCV formats"""

    @staticmethod
    def qimage_to_cv2(qimage: QImage) -> Optional[np.ndarray]:
        """Convert QImage to OpenCV numpy array"""
        try:
            if qimage.isNull():
                return None

            # Get image properties
            width = qimage.width()
            height = qimage.height()

            # Handle different formats
            if qimage.format() == QImage.Format_RGB32:
                # ARGB format
                ptr = qimage.constBits()
                arr = np.array(ptr).reshape(height, width, 4)
                # Convert ARGB to BGR (OpenCV format)
                bgr = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
                return bgr

            elif qimage.format() == QImage.Format_RGB888:
                # RGB format
                ptr = qimage.constBits()
                arr = np.array(ptr).reshape(height, width, 3)
                # Convert RGB to BGR
                bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                return bgr

            elif qimage.format() == QImage.Format_RGBA8888:
                # RGBA format
                ptr = qimage.constBits()
                arr = np.array(ptr).reshape(height, width, 4)
                # Convert RGBA to BGR
                bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
                return bgr

            else:
                # Convert to RGB32 first, then process
                converted = qimage.convertToFormat(QImage.Format_RGB32)
                return OpenCVBridge.qimage_to_cv2(converted)

        except Exception as e:
            print(f"Error converting QImage to OpenCV: {e}")
            return None

    @staticmethod
    def cv2_to_qimage(cv_img: np.ndarray) -> Optional[QImage]:
        """Convert OpenCV numpy array to QImage"""
        try:
            if cv_img is None or cv_img.size == 0:
                return None

            height, width = cv_img.shape[:2]

            # Handle different channel configurations
            if len(cv_img.shape) == 3:
                channels = cv_img.shape[2]

                if channels == 3:
                    # BGR to RGB conversion
                    rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                    bytes_per_line = 3 * width

                    qimage = QImage(
                        rgb_image.data,
                        width,
                        height,
                        bytes_per_line,
                        QImage.Format_RGB888
                    )
                    return qimage.copy()  # Create independent copy

                elif channels == 4:
                    # BGRA to RGBA conversion
                    rgba_image = cv2.cvtColor(cv_img, cv2.COLOR_BGRA2RGBA)
                    bytes_per_line = 4 * width

                    qimage = QImage(
                        rgba_image.data,
                        width,
                        height,
                        bytes_per_line,
                        QImage.Format_RGBA8888
                    )
                    return qimage.copy()

            elif len(cv_img.shape) == 2:
                # Grayscale image
                bytes_per_line = width

                qimage = QImage(
                    cv_img.data,
                    width,
                    height,
                    bytes_per_line,
                    QImage.Format_Grayscale8
                )
                return qimage.copy()

            return None

        except Exception as e:
            print(f"Error converting OpenCV to QImage: {e}")
            return None

    @staticmethod
    def qpixmap_to_cv2(pixmap: QPixmap) -> Optional[np.ndarray]:
        """Convert QPixmap to OpenCV numpy array"""
        if pixmap.isNull():
            return None

        qimage = pixmap.toImage()
        return OpenCVBridge.qimage_to_cv2(qimage)

    @staticmethod
    def cv2_to_qpixmap(cv_img: np.ndarray) -> Optional[QPixmap]:
        """Convert OpenCV numpy array to QPixmap"""
        qimage = OpenCVBridge.cv2_to_qimage(cv_img)
        if qimage:
            return QPixmap.fromImage(qimage)
        return None

    @staticmethod
    def qvideoframe_to_cv2(video_frame: QVideoFrame) -> Optional[np.ndarray]:
        """Convert QVideoFrame to OpenCV numpy array"""
        try:
            if not video_frame.isValid():
                return None

            # Map the frame for reading
            if not video_frame.map(QVideoFrame.ReadOnly):
                return None

            try:
                # Convert to QImage first
                qimage = video_frame.toImage()
                if qimage.isNull():
                    return None

                # Convert QImage to OpenCV
                cv_img = OpenCVBridge.qimage_to_cv2(qimage)
                return cv_img

            finally:
                # Always unmap the frame
                video_frame.unmap()

        except Exception as e:
            print(f"Error converting QVideoFrame to OpenCV: {e}")
            video_frame.unmap()
            return None


class ImageProcessor:
    """Image processing utilities using OpenCV"""

    @staticmethod
    def resize_image(
        image: np.ndarray,
        target_size: Tuple[int, int],
        keep_aspect_ratio: bool = True,
        interpolation: int = cv2.INTER_LINEAR
    ) -> np.ndarray:
        """Resize image with optional aspect ratio preservation"""
        height, width = image.shape[:2]
        target_width, target_height = target_size

        if keep_aspect_ratio:
            # Calculate scaling factor
            scale = min(target_width / width, target_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)

            # Resize image
            resized = cv2.resize(image, (new_width, new_height), interpolation=interpolation)

            # Create background and center the image
            result = np.zeros((target_height, target_width, image.shape[2]), dtype=image.dtype)
            y_offset = (target_height - new_height) // 2
            x_offset = (target_width - new_width) // 2
            result[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = resized

            return result
        else:
            return cv2.resize(image, target_size, interpolation=interpolation)

    @staticmethod
    def apply_blur(image: np.ndarray, blur_strength: float = 1.0) -> np.ndarray:
        """Apply Gaussian blur to image"""
        kernel_size = max(1, int(blur_strength * 5))
        if kernel_size % 2 == 0:
            kernel_size += 1
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), blur_strength)

    @staticmethod
    def adjust_brightness_contrast(
        image: np.ndarray,
        brightness: float = 0.0,
        contrast: float = 1.0
    ) -> np.ndarray:
        """Adjust brightness and contrast"""
        return cv2.convertScaleAbs(image, alpha=contrast, beta=brightness)

    @staticmethod
    def apply_sharpening(image: np.ndarray, strength: float = 1.0) -> np.ndarray:
        """Apply unsharp mask sharpening"""
        # Create Gaussian blur
        blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=1.0)

        # Create sharpened image
        sharpened = cv2.addWeighted(image, 1.0 + strength, blurred, -strength, 0)

        return sharpened

    @staticmethod
    def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale"""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    @staticmethod
    def add_watermark(
        image: np.ndarray,
        text: str,
        position: Tuple[int, int] = (10, 30),
        font_scale: float = 1.0,
        color: Tuple[int, int, int] = (255, 255, 255),
        thickness: int = 2
    ) -> np.ndarray:
        """Add text watermark to image"""
        result = image.copy()
        cv2.putText(
            result,
            text,
            position,
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA
        )
        return result

    @staticmethod
    def crop_image(
        image: np.ndarray,
        x: int, y: int,
        width: int, height: int
    ) -> np.ndarray:
        """Crop image to specified rectangle"""
        h, w = image.shape[:2]

        # Clamp coordinates to image bounds
        x = max(0, min(x, w))
        y = max(0, min(y, h))
        width = max(1, min(width, w - x))
        height = max(1, min(height, h - y))

        return image[y:y+height, x:x+width]

    @staticmethod
    def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by specified angle (degrees)"""
        height, width = image.shape[:2]
        center = (width // 2, height // 2)

        # Create rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

        # Calculate new bounding box
        cos_val = abs(rotation_matrix[0, 0])
        sin_val = abs(rotation_matrix[0, 1])
        new_width = int(height * sin_val + width * cos_val)
        new_height = int(height * cos_val + width * sin_val)

        # Adjust translation
        rotation_matrix[0, 2] += (new_width - width) / 2
        rotation_matrix[1, 2] += (new_height - height) / 2

        # Apply rotation
        rotated = cv2.warpAffine(image, rotation_matrix, (new_width, new_height))
        return rotated

    @staticmethod
    def detect_edges(image: np.ndarray, threshold1: float = 100, threshold2: float = 200) -> np.ndarray:
        """Detect edges using Canny edge detector"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        edges = cv2.Canny(gray, threshold1, threshold2)
        return edges

    @staticmethod
    def apply_histogram_equalization(image: np.ndarray) -> np.ndarray:
        """Apply histogram equalization to improve contrast"""
        if len(image.shape) == 3:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            # Convert back to BGR
            return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            # Grayscale image
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            return clahe.apply(image)


class ColorUtils:
    """Color conversion and manipulation utilities"""

    @staticmethod
    def qcolor_to_bgr(qcolor: QColor) -> Tuple[int, int, int]:
        """Convert QColor to BGR tuple for OpenCV"""
        return (qcolor.blue(), qcolor.green(), qcolor.red())

    @staticmethod
    def bgr_to_qcolor(bgr: Tuple[int, int, int]) -> QColor:
        """Convert BGR tuple to QColor"""
        b, g, r = bgr
        return QColor(r, g, b)

    @staticmethod
    def hex_to_bgr(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color string to BGR tuple"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (b, g, r)

    @staticmethod
    def bgr_to_hex(bgr: Tuple[int, int, int]) -> str:
        """Convert BGR tuple to hex color string"""
        b, g, r = bgr
        return f"#{r:02x}{g:02x}{b:02x}"


class VideoFrameUtils:
    """Utilities for working with video frames"""

    @staticmethod
    def extract_frame_info(video_frame: QVideoFrame) -> dict:
        """Extract metadata from video frame"""
        if not video_frame.isValid():
            return {}

        return {
            "width": video_frame.width(),
            "height": video_frame.height(),
            "pixel_format": video_frame.pixelFormat(),
            "start_time": video_frame.startTime(),
            "end_time": video_frame.endTime(),
            "is_readable": video_frame.isReadable(),
            "is_writable": video_frame.isWritable(),
        }

    @staticmethod
    def create_thumbnail_from_frame(
        video_frame: QVideoFrame,
        thumbnail_size: QSize = QSize(160, 120)
    ) -> Optional[QPixmap]:
        """Create thumbnail from video frame"""
        try:
            # Convert to OpenCV format
            cv_img = OpenCVBridge.qvideoframe_to_cv2(video_frame)
            if cv_img is None:
                return None

            # Resize to thumbnail size
            resized = ImageProcessor.resize_image(
                cv_img,
                (thumbnail_size.width(), thumbnail_size.height()),
                keep_aspect_ratio=True
            )

            # Convert back to QPixmap
            return OpenCVBridge.cv2_to_qpixmap(resized)

        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return None