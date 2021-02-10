lines = []

with open('commands.txt', 'r') as f:
    lines = f.readlines()

with open('commands.txt', 'w') as f:
    lines = lines[2:]
    lines = lines[:-2]
    f.writelines(lines)