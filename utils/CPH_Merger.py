cph_main = open('CustomParamHandler.py', 'r')
cph_config = open('CPH_Config.py', 'r')


def write_cph_imports():
    line = cph_main.readline()
    while line:
        if line == 'from CPH_Config import MainTab\n':
            line = cph_main.readline()
            continue
        merged_file.write(line)
        if line == '#  End CustomParameterHandler.py Imports\n':
            merged_file.write(cph_main.readline())
            merged_file.write('\n')
            break
        line = cph_main.readline()


def write_config_imports():
    line = cph_config.readline()
    while line:
        if line == 'from Quickstart import Quickstart\n':
            line = cph_config.readline()
            continue
        merged_file.write(line)
        if line == '#  End CPH_Config.py Imports\n':
            merged_file.write(cph_config.readline())
            merged_file.write('\n')
            break
        line = cph_config.readline()


with open('CustomParamHandler_merged.py', 'w') as merged_file:
    write_cph_imports()
    write_config_imports()
    with open('Quickstart.py', 'r') as quickstart:
        merged_file.write(quickstart.read())
    for line in cph_config.readlines():
        merged_file.write(line)
    for line in cph_main.readlines():
        merged_file.write(line)

cph_main.close()
cph_config.close()