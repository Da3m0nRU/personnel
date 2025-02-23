import os


def merge_cs_files(folder_path, output_file):
    with open(output_file, 'w', encoding='utf-8') as out_f:  # Specify encoding here
        for root, dirs, files in os.walk(folder_path):
            for file_name in files:
                if file_name.endswith('.py'):
                    file_path = os.path.join(root, file_name)
                    # Получаем относительный путь к файлу относительно folder_path
                    relative_path = os.path.relpath(file_path, folder_path)
                    # Удаляем дублирующуюся часть пути, если она есть
                    relative_path = relative_path.replace(
                        relative_path.split(os.sep)[0] + os.sep, '', 1)
                    with open(file_path, 'r', encoding='utf-8') as in_f:  # Specify encoding here
                        # Записываем относительный путь и название файла
                        out_f.write(
                            f"File directory: {relative_path}, and it contains following code: \n")
                        out_f.write(in_f.read())
                        out_f.write("\n\n")


# Укажите путь к папке, содержащей .cs файлы, и имя выходного файла
folder_path = "G:/вуз мгимо/3 курс/Программный Проект/Project"
output_file = "output.txt"

merge_cs_files(folder_path, output_file)
