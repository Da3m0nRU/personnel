import os


def merge_files(folder_path, output_file, extensions):
    with open(output_file, 'w', encoding='utf-8') as out_f:
        for root, dirs, files in os.walk(folder_path):
            for file_name in files:
                if any(file_name.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file_name)
                    # Получаем относительный путь к файлу относительно folder_path
                    relative_path = os.path.relpath(file_path, folder_path)
                    # Удаляем дублирующуюся часть пути, если она есть
                    relative_path = relative_path.replace(
                        relative_path.split(os.sep)[0] + os.sep, '', 1)

                    # Для файлов с русскими комментариями лучше использовать cp1251
                    try:
                        with open(file_path, 'r', encoding='cp1251') as in_f:
                            file_content = in_f.read()
                    except UnicodeDecodeError:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as in_f:
                                file_content = in_f.read()
                        except UnicodeDecodeError:
                            try:
                                with open(file_path, 'r', encoding='latin-1') as in_f:
                                    file_content = in_f.read()
                            except:
                                out_f.write(
                                    f"File directory: {relative_path}, could not decode file\n\n")
                                continue

                    # Записываем относительный путь и название файла
                    out_f.write(
                        f"File directory: {relative_path}, and it contains following code: \n")
                    out_f.write(file_content)
                    out_f.write("\n\n")


# Используем текущую директорию в качестве folder_path
folder_path = os.path.dirname(os.path.abspath(__file__))
output_file = "output.txt"
extensions = ['.py', '.h']  # Расширения файлов для поиска

merge_files(folder_path, output_file, extensions)
