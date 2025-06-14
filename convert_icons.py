import os
from cairosvg import svg2png

def convert_svg_to_png(input_dir, output_dir):
    # Создаем выходную директорию, если её нет
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Конвертируем каждый SVG файл
    for filename in os.listdir(input_dir):
        if filename.endswith('.svg'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename.replace('.svg', '.png'))
            
            try:
                # Конвертируем SVG в PNG
                svg2png(url=input_path, write_to=output_path)
                print(f"Конвертирован: {filename} -> {os.path.basename(output_path)}")
            except Exception as e:
                print(f"Ошибка при конвертации {filename}: {str(e)}")

if __name__ == "__main__":
    # Пути к директориям
    input_dir = "icons"  # директория с SVG файлами
    output_dir = "icons"  # та же директория для PNG файлов
    
    # Конвертируем файлы
    convert_svg_to_png(input_dir, output_dir)
    print("\nКонвертация завершена!") 