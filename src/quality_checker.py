"""
Quality Checker Module for Railway QR Code System
AI-based quality verification for generated QR codes
"""

import cv2
import numpy as np
from PIL import Image
import qrcode
from typing import Dict, List, Tuple
import os

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import QUALITY_THRESHOLD, MIN_QR_SIZE


class RailwayQRQualityChecker:
    """AI-based quality verification for railway QR codes"""
    
    def __init__(self):
        self.quality_threshold = QUALITY_THRESHOLD
        self.min_qr_size = MIN_QR_SIZE
    
    def verify_qr_quality(self, qr_image_path: str) -> Dict:
        """
        Use AI/CV to check QR code quality
        
        Parameters:
        - qr_image_path: str (path to QR image file)
        
        Returns:
        - quality_result: dict with quality_score, is_readable, issues
        """
        
        try:
            # Load image
            image = cv2.imread(qr_image_path)
            if image is None:
                return {
                    'quality_score': 0,
                    'is_readable': False,
                    'issues': ['Could not load image file'],
                    'detailed_analysis': {}
                }
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Perform quality checks
            size_score = self._check_size(gray)
            contrast_score = self._check_contrast(gray)
            sharpness_score = self._check_sharpness(gray)
            alignment_score = self._check_alignment(gray)
            readability_score = self._check_readability(qr_image_path)
            
            # Calculate overall quality score
            quality_score = (
                size_score * 0.2 +
                contrast_score * 0.25 +
                sharpness_score * 0.25 +
                alignment_score * 0.15 +
                readability_score * 0.15
            )
            
            # Determine if readable
            is_readable = quality_score >= self.quality_threshold and readability_score > 50
            
            # Collect issues
            issues = []
            if size_score < 70:
                issues.append("QR code size is too small")
            if contrast_score < 70:
                issues.append("Poor contrast between black and white areas")
            if sharpness_score < 70:
                issues.append("QR code appears blurry or out of focus")
            if alignment_score < 70:
                issues.append("QR code alignment markers are distorted")
            if readability_score < 50:
                issues.append("QR code cannot be read by standard scanners")
            
            detailed_analysis = {
                'size_score': size_score,
                'contrast_score': contrast_score,
                'sharpness_score': sharpness_score,
                'alignment_score': alignment_score,
                'readability_score': readability_score,
                'image_dimensions': gray.shape,
                'file_size': os.path.getsize(qr_image_path) if os.path.exists(qr_image_path) else 0
            }
            
            return {
                'quality_score': round(quality_score, 2),
                'is_readable': is_readable,
                'issues': issues,
                'detailed_analysis': detailed_analysis
            }
            
        except Exception as e:
            return {
                'quality_score': 0,
                'is_readable': False,
                'issues': [f'Quality check failed: {str(e)}'],
                'detailed_analysis': {}
            }
    
    def _check_size(self, gray_image: np.ndarray) -> float:
        """Check if QR code size is adequate"""
        
        height, width = gray_image.shape
        
        # Check if image is large enough
        min_dimension = min(height, width)
        
        if min_dimension < self.min_qr_size:
            return 0
        
        # Score based on size (larger is generally better for laser marking)
        size_score = min(100, (min_dimension / self.min_qr_size) * 100)
        
        return size_score
    
    def _check_contrast(self, gray_image: np.ndarray) -> float:
        """Check contrast between black and white areas"""
        
        # Calculate histogram
        hist = cv2.calcHist([gray_image], [0], None, [256], [0, 256])
        
        # Find peaks for black and white
        black_peak = np.argmax(hist[:128])  # Dark areas
        white_peak = np.argmax(hist[128:]) + 128  # Bright areas
        
        # Calculate contrast ratio
        contrast_ratio = (white_peak - black_peak) / 255.0
        
        # Score based on contrast (higher is better)
        contrast_score = min(100, contrast_ratio * 200)
        
        return contrast_score
    
    def _check_sharpness(self, gray_image: np.ndarray) -> float:
        """Check image sharpness using Laplacian variance"""
        
        # Apply Laplacian filter
        laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
        
        # Calculate variance
        sharpness = laplacian.var()
        
        # Normalize score (typical range is 0-1000, we want 0-100)
        sharpness_score = min(100, sharpness / 10)
        
        return sharpness_score
    
    def _check_alignment(self, gray_image: np.ndarray) -> float:
        """Check QR code alignment markers"""
        
        # Convert to binary
        _, binary = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Look for square contours (alignment markers)
        square_contours = 0
        for contour in contours:
            # Approximate contour
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Check if it's roughly square
            if len(approx) == 4:
                area = cv2.contourArea(contour)
                if area > 100:  # Minimum area for alignment marker
                    square_contours += 1
        
        # Score based on number of detected alignment markers
        # QR codes should have at least 3 alignment markers
        alignment_score = min(100, (square_contours / 3) * 100)
        
        return alignment_score
    
    def _check_readability(self, qr_image_path: str) -> float:
        """Check if QR code can actually be read"""
        
        try:
            # Try to decode the QR code
            image = cv2.imread(qr_image_path)
            detector = cv2.QRCodeDetector()
            
            data, bbox, _ = detector.detectAndDecode(image)
            
            if data:
                # QR code was successfully read
                return 100
            else:
                # QR code could not be read
                return 0
                
        except Exception:
            return 0
    
    def batch_quality_check(self, qr_files: List[str]) -> Dict:
        """
        Perform quality check on multiple QR codes
        
        Parameters:
        - qr_files: list of QR code file paths
        
        Returns:
        - batch_results: dict with summary and individual results
        """
        
        results = []
        total_score = 0
        readable_count = 0
        
        for qr_file in qr_files:
            if os.path.exists(qr_file):
                result = self.verify_qr_quality(qr_file)
                result['filename'] = os.path.basename(qr_file)
                results.append(result)
                
                total_score += result['quality_score']
                if result['is_readable']:
                    readable_count += 1
        
        # Calculate summary statistics
        avg_score = total_score / len(results) if results else 0
        readability_rate = (readable_count / len(results)) * 100 if results else 0
        
        return {
            'total_files': len(qr_files),
            'processed_files': len(results),
            'average_quality_score': round(avg_score, 2),
            'readability_rate': round(readability_rate, 2),
            'readable_count': readable_count,
            'individual_results': results
        }
    
    def generate_quality_report(self, batch_results: Dict, output_path: str) -> bool:
        """
        Generate quality report as CSV
        
        Parameters:
        - batch_results: dict from batch_quality_check
        - output_path: str (output CSV file path)
        
        Returns:
        - success: bool
        """
        
        try:
            import pandas as pd
            
            # Prepare data for CSV
            report_data = []
            
            for result in batch_results['individual_results']:
                report_data.append({
                    'Filename': result['filename'],
                    'Quality_Score': result['quality_score'],
                    'Is_Readable': result['is_readable'],
                    'Issues': '; '.join(result['issues']),
                    'Size_Score': result['detailed_analysis'].get('size_score', 0),
                    'Contrast_Score': result['detailed_analysis'].get('contrast_score', 0),
                    'Sharpness_Score': result['detailed_analysis'].get('sharpness_score', 0),
                    'Alignment_Score': result['detailed_analysis'].get('alignment_score', 0),
                    'Readability_Score': result['detailed_analysis'].get('readability_score', 0),
                    'Image_Width': result['detailed_analysis'].get('image_dimensions', (0, 0))[1],
                    'Image_Height': result['detailed_analysis'].get('image_dimensions', (0, 0))[0],
                    'File_Size_Bytes': result['detailed_analysis'].get('file_size', 0)
                })
            
            # Create DataFrame and save
            df = pd.DataFrame(report_data)
            df.to_csv(output_path, index=False)
            
            return True
            
        except Exception as e:
            print(f"Error generating quality report: {e}")
            return False
    
    def suggest_improvements(self, quality_result: Dict) -> List[str]:
        """
        Suggest improvements based on quality analysis
        
        Parameters:
        - quality_result: dict from verify_qr_quality
        
        Returns:
        - suggestions: list of improvement suggestions
        """
        
        suggestions = []
        analysis = quality_result.get('detailed_analysis', {})
        
        if analysis.get('size_score', 0) < 70:
            suggestions.append("Increase QR code size for better laser marking visibility")
        
        if analysis.get('contrast_score', 0) < 70:
            suggestions.append("Improve contrast by using pure black (#000000) and white (#FFFFFF)")
        
        if analysis.get('sharpness_score', 0) < 70:
            suggestions.append("Ensure QR code is generated at high resolution (300+ DPI)")
        
        if analysis.get('alignment_score', 0) < 70:
            suggestions.append("Check QR code alignment markers for distortion")
        
        if analysis.get('readability_score', 0) < 50:
            suggestions.append("QR code failed readability test - regenerate with higher quality settings")
        
        if not suggestions:
            suggestions.append("QR code quality is excellent - suitable for laser marking")
        
        return suggestions


if __name__ == "__main__":
    # Test the quality checker
    checker = RailwayQRQualityChecker()
    
    # Test with a sample QR code (if it exists)
    test_file = "output/qr_codes/test.png"
    
    if os.path.exists(test_file):
        result = checker.verify_qr_quality(test_file)
        print(f"Quality Score: {result['quality_score']}")
        print(f"Is Readable: {result['is_readable']}")
        print(f"Issues: {result['issues']}")
        
        suggestions = checker.suggest_improvements(result)
        print(f"Suggestions: {suggestions}")
    else:
        print("No test QR code found. Generate one first to test quality checking.")
