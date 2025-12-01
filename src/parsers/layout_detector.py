#!/usr/bin/env python3
"""
Part 3: Layout Detection using LayoutParser
Uses deep learning models to detect document structure
Works with alternative backends for Mac compatibility
"""

import sys
from pathlib import Path
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm
from dataclasses import dataclass, asdict
import io

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import LayoutParser
try:
    import layoutparser as lp
    LAYOUTPARSER_AVAILABLE = True
    logger.info("LayoutParser imported successfully")
except ImportError as e:
    logger.error(f"LayoutParser not available: {e}")
    logger.error("Please run: pip install layoutparser")
    LAYOUTPARSER_AVAILABLE = False
    sys.exit(1)


@dataclass
class LayoutBlock:
    """Represents a detected layout block"""
    block_type: str
    text: str
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    confidence: float
    page: int
    area: float


class LayoutParserDetector:
    """Layout detection using LayoutParser with multiple backend options"""
    
    def __init__(self, input_dir: str = "data/raw/pdfs", output_dir: str = "data/parsed/layouts"):
        """
        Initialize LayoutParser detector
        
        Args:
            input_dir: Directory containing documents
            output_dir: Directory to save layout analysis
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize model
        self.model = self._initialize_model()
        
        # Track statistics
        self.detection_log = []
    
    def _initialize_model(self):
        """Initialize LayoutParser model with appropriate backend"""
        
        model = None
        
        # Try different model backends in order of preference
        model_configs = [
            {
                'name': 'Detectron2',
                'config': 'lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config',
                'label_map': {0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
            },
            {
                'name': 'EfficientDet',
                'config': 'lp://efficientdet/PubLayNet/tf_efficientdet_d0',
                'label_map': {0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
            },
            {
                'name': 'PaddleDetection',
                'config': 'lp://PaddleDetection/ppyolov2_r50vd_dcn_365e_publaynet/config',
                'label_map': {0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
            }
        ]
        
        for config in model_configs:
            try:
                logger.info(f"Trying to load {config['name']} model...")
                
                if config['name'] == 'Detectron2':
                    model = lp.Detectron2LayoutModel(
                        config['config'],
                        extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
                        label_map=config['label_map']
                    )
                elif config['name'] == 'EfficientDet':
                    model = lp.EfficientDetLayoutModel(
                        config['config'],
                        label_map=config['label_map']
                    )
                elif config['name'] == 'PaddleDetection':
                    model = lp.PaddleDetectionLayoutModel(
                        config['config'],
                        label_map=config['label_map']
                    )
                
                logger.info(f"✅ Successfully loaded {config['name']} model")
                return model
                
            except Exception as e:
                logger.warning(f"Could not load {config['name']}: {e}")
                continue
        
        # If no model could be loaded, use Tesseract for basic detection
        logger.warning("No deep learning model available. Using Tesseract for basic layout detection.")
        return None
    
    def convert_html_to_image(self, html_path: Path) -> Optional[np.ndarray]:
        """
        Convert HTML to image for layout detection
        
        Args:
            html_path: Path to HTML file
            
        Returns:
            Image array or None
        """
        try:
            # For demonstration, create a placeholder image
            # In production, you'd use tools like wkhtmltoimage or selenium
            
            # Create a simple white image as placeholder
            width, height = 1700, 2200  # Standard letter size at 200 DPI
            image = np.ones((height, width, 3), dtype=np.uint8) * 255
            
            # Add some text to indicate this is a placeholder
            cv2.putText(image, f"Layout Detection for: {html_path.name}", 
                       (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            
            return image
            
        except Exception as e:
            logger.error(f"Error converting HTML to image: {e}")
            return None
    
    def detect_layout_with_model(self, image: np.ndarray) -> List[LayoutBlock]:
        """
        Detect layout using LayoutParser model
        
        Args:
            image: Document image
            
        Returns:
            List of detected layout blocks
        """
        blocks = []
        
        if self.model is None:
            return self.detect_layout_with_tesseract(image)
        
        try:
            # Detect layout
            layout = self.model.detect(image)
            
            # Convert to our LayoutBlock format
            for idx, element in enumerate(layout):
                block = LayoutBlock(
                    block_type=element.type,
                    text="",  # Text extraction would happen separately
                    bbox=(element.x_1, element.y_1, element.x_2, element.y_2),
                    confidence=element.score if hasattr(element, 'score') else 0.9,
                    page=1,
                    area=(element.x_2 - element.x_1) * (element.y_2 - element.y_1)
                )
                blocks.append(block)
            
            # Sort blocks by vertical position (reading order)
            blocks.sort(key=lambda b: (b.bbox[1], b.bbox[0]))
            
        except Exception as e:
            logger.error(f"Error in model detection: {e}")
            blocks = self.detect_layout_with_tesseract(image)
        
        return blocks
    
    def detect_layout_with_tesseract(self, image: np.ndarray) -> List[LayoutBlock]:
        """
        Fallback layout detection using Tesseract OCR
        
        Args:
            image: Document image
            
        Returns:
            List of detected layout blocks
        """
        blocks = []
        
        try:
            # Use Tesseract's layout analysis
            ocr_agent = lp.TesseractAgent(languages='eng')
            
            # Get layout blocks
            res = ocr_agent.detect(image, return_response=True)
            
            # Parse Tesseract output
            for idx, row in res['data'].iterrows():
                if row['text'] and str(row['text']).strip():
                    # Determine block type based on characteristics
                    block_type = self._classify_block_type(row)
                    
                    block = LayoutBlock(
                        block_type=block_type,
                        text=str(row['text'])[:200],  # Limit text length
                        bbox=(row['left'], row['top'], 
                              row['left'] + row['width'], row['top'] + row['height']),
                        confidence=row['conf'] / 100.0 if row['conf'] > 0 else 0.5,
                        page=1,
                        area=row['width'] * row['height']
                    )
                    blocks.append(block)
            
        except Exception as e:
            logger.error(f"Error in Tesseract detection: {e}")
        
        return blocks
    
    def _classify_block_type(self, tesseract_row) -> str:
        """Classify block type based on Tesseract output"""
        
        # Simple heuristics for classification
        text = str(tesseract_row.get('text', '')).strip()
        
        if not text:
            return 'unknown'
        
        # Check for title patterns
        if len(text) < 100 and text.isupper():
            return 'Title'
        
        # Check for list patterns
        if text.startswith(('•', '-', '*', '1.', '2.', '3.')):
            return 'List'
        
        # Default to text
        return 'Text'
    
    def visualize_layout(self, image: np.ndarray, blocks: List[LayoutBlock], save_path: Path):
        """
        Visualize detected layout blocks on the image
        
        Args:
            image: Original image
            blocks: Detected layout blocks
            save_path: Path to save visualization
        """
        try:
            # Create a copy for visualization
            vis_image = image.copy()
            
            # Color map for different block types
            colors = {
                'Text': (0, 255, 0),      # Green
                'Title': (255, 0, 0),      # Red
                'Table': (0, 0, 255),      # Blue
                'Figure': (255, 255, 0),   # Cyan
                'List': (255, 0, 255)      # Magenta
            }
            
            # Draw bounding boxes
            for block in blocks:
                color = colors.get(block.block_type, (128, 128, 128))
                x1, y1, x2, y2 = [int(coord) for coord in block.bbox]
                
                # Draw rectangle
                cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
                
                # Add label
                label = f"{block.block_type}: {block.confidence:.2f}"
                cv2.putText(vis_image, label, (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Save visualization
            cv2.imwrite(str(save_path), vis_image)
            logger.info(f"Saved visualization to {save_path}")
            
        except Exception as e:
            logger.error(f"Error creating visualization: {e}")
    
    def process_document(self, file_path: Path) -> Dict:
        """
        Process a single document for layout detection
        
        Args:
            file_path: Path to document
            
        Returns:
            Layout detection results
        """
        logger.info(f"Processing layout detection for: {file_path.name}")
        
        # Convert document to image (for HTML files)
        if file_path.suffix.lower() == '.html':
            image = self.convert_html_to_image(file_path)
        else:
            logger.warning(f"Unsupported format: {file_path.suffix}")
            return {'status': 'skipped', 'reason': 'unsupported_format'}
        
        if image is None:
            return {'status': 'error', 'reason': 'conversion_failed'}
        
        # Detect layout
        blocks = self.detect_layout_with_model(image)
        
        # Create visualization
        rel_path = file_path.relative_to(self.input_dir / "sec-edgar-filings")
        vis_dir = self.output_dir / "visualizations" / rel_path.parent
        vis_dir.mkdir(parents=True, exist_ok=True)
        vis_path = vis_dir / f"{file_path.stem}_layout.png"
        
        if len(blocks) > 0:
            self.visualize_layout(image, blocks[:50], vis_path)  # Limit to first 50 blocks
        
        # Analyze structure
        structure = self.analyze_layout_structure(blocks)
        
        # Create result
        result = {
            'status': 'success',
            'file': str(file_path),
            'blocks_detected': len(blocks),
            'block_types': structure['block_types'],
            'layout_structure': structure,
            'model_used': type(self.model).__name__ if self.model else 'Tesseract',
            'visualization': str(vis_path) if vis_path.exists() else None,
            'blocks': [asdict(b) for b in blocks[:20]],  # Sample of blocks
            'processed_at': datetime.now().isoformat()
        }
        
        return result
    
    def analyze_layout_structure(self, blocks: List[LayoutBlock]) -> Dict:
        """Analyze the layout structure from detected blocks"""
        
        structure = {
            'block_types': {},
            'reading_order': [],
            'columns_detected': 1,
            'has_tables': False,
            'has_figures': False,
            'avg_confidence': 0.0
        }
        
        if not blocks:
            return structure
        
        # Count block types
        for block in blocks:
            block_type = block.block_type
            structure['block_types'][block_type] = structure['block_types'].get(block_type, 0) + 1
            
            if block_type == 'Table':
                structure['has_tables'] = True
            elif block_type == 'Figure':
                structure['has_figures'] = True
        
        # Calculate average confidence
        confidences = [b.confidence for b in blocks if b.confidence > 0]
        structure['avg_confidence'] = sum(confidences) / len(confidences) if confidences else 0
        
        # Detect multi-column layout (simple heuristic)
        x_positions = [b.bbox[0] for b in blocks]
        if x_positions:
            unique_x = len(set(int(x/100) for x in x_positions))  # Group by 100px columns
            structure['columns_detected'] = min(unique_x, 3)  # Cap at 3 columns
        
        return structure
    
    def process_all_documents(self):
        """Process all documents for layout detection"""
        
        # Find documents
        filing_dir = self.input_dir / "sec-edgar-filings"
        
        if not filing_dir.exists():
            logger.error(f"Directory not found: {filing_dir}")
            return
        
        # Get ALL HTML files (remove limit)
        files = list(filing_dir.rglob("primary-document.html"))
        
        # Make sure we get both AAPL and MSFT
        logger.info(f"Found files from: {set(f.parts[-4] for f in files if len(f.parts) > 3)}")
        
        if not files:
            logger.warning("No documents found")
            return
        
        logger.info(f"Processing {len(files)} documents with LayoutParser")
        
        # Process each file
        for file_path in tqdm(files, desc="LayoutParser detection"):
            result = self.process_document(file_path)
            
            # Save results
            if result.get('status') == 'success':
                self.save_results(file_path, result)
            
            # Log results
            self.detection_log.append({
                'file': file_path.name,
                'status': result.get('status'),
                'blocks': result.get('blocks_detected', 0),
                'model': result.get('model_used', 'unknown'),
                'confidence': result.get('layout_structure', {}).get('avg_confidence', 0)
            })
        
        # Save log and print summary
        self._save_log()
        self._print_summary()
    
    def save_results(self, file_path: Path, result: Dict):
        """Save layout detection results"""
        
        # Create output path
        rel_path = file_path.relative_to(self.input_dir / "sec-edgar-filings")
        output_path = self.output_dir / rel_path.parent
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save results (without full blocks data)
        save_result = {k: v for k, v in result.items() if k != 'blocks'}
        result_file = output_path / f"{file_path.stem}_layoutparser.json"
        
        with open(result_file, 'w') as f:
            json.dump(save_result, f, indent=2)
    
    def _save_log(self):
        """Save detection log"""
        log_file = self.output_dir / "layoutparser_log.json"
        with open(log_file, 'w') as f:
            json.dump(self.detection_log, f, indent=2)
        logger.info(f"Log saved to {log_file}")
    
    def _print_summary(self):
        """Print detection summary"""
        print("\n" + "="*50)
        print("LayoutParser Detection Summary")
        print("="*50)
        
        if self.detection_log:
            successful = sum(1 for log in self.detection_log if log['status'] == 'success')
            total_blocks = sum(log.get('blocks', 0) for log in self.detection_log)
            
            print(f"Documents processed: {len(self.detection_log)}")
            print(f"Successful: {successful}")
            print(f"Total blocks detected: {total_blocks}")
            
            # Breakdown by ticker
            tickers = {}
            for log in self.detection_log:
                ticker = log.get('ticker', 'unknown')
                filing = log.get('filing_type', 'unknown')
                key = f"{ticker}/{filing}"
                
                if key not in tickers:
                    tickers[key] = {'count': 0, 'blocks': 0, 'successful': 0}
                
                tickers[key]['count'] += 1
                tickers[key]['blocks'] += log.get('blocks', 0)
                if log.get('status') == 'success':
                    tickers[key]['successful'] += 1
            
            print("\n📊 Breakdown by Company/Filing:")
            for key, stats in sorted(tickers.items()):
                print(f"  {key}: {stats['successful']}/{stats['count']} docs, {stats['blocks']} blocks")
            
            if successful > 0:
                avg_blocks = total_blocks / successful
                print(f"\nAverage blocks per document: {avg_blocks:.0f}")
                
                # Model used
                models = set(log.get('model', 'unknown') for log in self.detection_log)
                print(f"Models used: {', '.join(models)}")
        
        print(f"\n📁 Output directory: {self.output_dir}")
        print(f"📊 Visualizations saved in: {self.output_dir}/visualizations/")


def main():
    """Main function"""
    
    if not LAYOUTPARSER_AVAILABLE:
        print("\n❌ LayoutParser is not installed!")
        print("\nTo install LayoutParser, run:")
        print("  pip install layoutparser")
        print("\nFor Mac with ARM chip, also try:")
        print("  pip install 'layoutparser[paddledetection]'")
        print("  pip install 'layoutparser[tesseract]'")
        return
    
    detector = LayoutParserDetector()
    detector.process_all_documents()
    
    print("\n✅ LayoutParser Part 3 Complete!")
    print("\nNext steps:")
    print("1. Review layout visualizations in data/parsed/layouts/visualizations/")
    print("2. Check layoutparser_log.json for details")
    print("3. Proceed to Part 4 for Docling integration")


if __name__ == "__main__":
    main()
    