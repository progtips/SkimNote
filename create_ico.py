import sys
import os
from PyQt6.QtSvgWidgets import QSvgWidget, QSvgRenderer
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtWidgets import QApplication
from PIL import Image

def svg_to_ico(svg_path, ico_path, sizes=[16, 32, 48, 64, 128, 256]):
    """Convert SVG to ICO with multiple sizes"""
    app = QApplication(sys.argv)
    renderer = QSvgRenderer(svg_path)
    images = []
    temp_files = []
    
    try:
        for size in sizes:
            pixmap = QPixmap(size, size)
            pixmap.fill()
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            temp_png = f"temp_{size}.png"
            pixmap.save(temp_png)
            temp_files.append(temp_png)
            images.append(Image.open(temp_png).convert('RGBA'))
        
        # Save as ICO
        images[0].save(ico_path, format='ICO', sizes=[(size, size) for size in sizes],
                      append_images=images[1:])
        
    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

if __name__ == '__main__':
    svg_to_ico('icons/app.svg', 'icons/app.ico') 