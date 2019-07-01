import collections
import datetime
import shutil
from typing import Any, Callable, List


Partition = collections.namedtuple("Partition", [
    'device',
    'mountpoint'
])


Meminfo = collections.namedtuple('Meminfo', [
    'total',
    'free',
    'cached',
    'used',
])


def term_length(line: str) -> int:
    action = 'COUNT'
    cursor = 0
    counter = 0

    for char in line:
        if action == 'COUNT' and char == '\u001B':
            action = 'SKIP'
        elif action == 'SKIP' and char == 'm':
            action = 'COUNT'
        elif action == 'COUNT':
            counter += 1

    return counter


def get_term_width() -> int:
    return shutil.get_terminal_size((37, 0)).columns


def print_with_cut(line: str) -> None:
    line_length = get_term_width()

    action = 'PRINT'
    counter = 0
    for char in line:
        if action == 'PRINT' and char == '\u001B':
            action = 'SKIP'
        elif action == 'SKIP' and char == 'm':
            action = 'PRINT'
        elif action == 'PRINT':
            counter += 1

            if counter > line_length:
                break

        print(char, end='')

    print('')


def print_center(*lines: str) -> None:
    max_length = max(term_length(line) for line in lines)
    line_length = get_term_width()
    margin_left = ' ' * round((line_length - max_length) / 2)

    for line in lines:
        print_with_cut(margin_left + line)


def get_fillers_for_table(table: List[List[str]]) -> List[List[str]]:
    table_rows = len(table)
    table_columns = len(table[0])

    fillers = [["" for _ in range(table_columns)] for _ in range(table_rows)]

    for column in range(table_columns):
        max_cell_in_column = 0

        for row in range(table_rows):
            cell = table[row][column]
            cell_length = term_length(cell)

            max_cell_in_column = max(max_cell_in_column, cell_length)

        for row in range(table_rows):
            cell = table[row][column]
            cell_length = term_length(cell)

            filler_length = max_cell_in_column - cell_length
            fillers[row][column] = ' ' * filler_length

    return fillers


def print_table(table: List[List[str]], justifiers: List[str]) -> None:
    fillers = get_fillers_for_table(table)

    lines = []
    for r, row in enumerate(table):
        line = ''
        for c, cell in enumerate(row):
            filler = fillers[r][c]
            justify = justifiers[c]

            if justify == 'LEFT':
                line += cell + filler + ' '
            else:
                line += filler + cell + ' '

        lines.append(line)

    print_center(*lines)


def show_banner() -> None:
    print_center(
        '\u001B[31m __ __ _____ __ __ _____ ___ _ _____ _____ ',
        '\u001B[31m|  |  |  ___|  |  |  ___|   | |_   _|     |',
        '\u001B[31m|     |  ___|     |  ___|     | | | |  -  |',
        '\u001B[35m|_|_|_|_____|_|_|_|_____|_|___| |_| |_____|',
    )

    print_center(
        '\u001B[35m __ __ _____ ____ _____ ',
        '\u001B[35m|  |  |     | __ \_   _|',
        '\u001B[33m|     |  -  |    <_| |_ ',
        '\u001B[33m|_|_|_|_____|_|__|_____|',
    )

    print_center(
        '\u001B[32m ____ _____ ____ ____ _____ ',
        '\u001B[32m|    |  _  | __ \ __ \  ___|',
        '\u001B[32m| ---|     |    <  __/  ___|',
        '\u001B[34m|____|__|__|_|__|_|  |_____|',
    )

    print_center(
        '\u001B[34m ___ _____ _____ __ __ ',
        '\u001B[34m|   \_   _|  ___|  |  |',
        '\u001B[36m| -  || |_|  ___|     |',
        '\u001B[36m|___/_____|_____|_|_|_|',
    )

    print()


def get_uptime() -> datetime.timedelta:
    with open('/proc/uptime') as fh:
        seconds = float(fh.read().split()[0])
        return datetime.timedelta(seconds=seconds)


def format_uptime(uptime: datetime.timedelta) -> str:
    if uptime.days > 0:
        result = '%d days, ' % uptime.days
    else:
        result = ''

    minutes = uptime.seconds / 60 % 60
    hours = uptime.seconds / 60 / 60 % 24

    result += '%d:%02d' % (hours, minutes)

    return result


def show_uptime() -> None:
    try:
        uptime = format_uptime(get_uptime())
    except PermissionError:
        uptime = '?'

    print_center('\u001B[34mup: \u001B[36m' + uptime + '\u001B[0m')
    print()


def get_device_short_name(long_name: str) -> str:
    if '/dev/sd' in long_name or '/dev/nvme' in long_name:
        return long_name[-4:]
    elif '/dev/mapper' in long_name:
        return long_name.split('-')[-1]
    elif '/dev/' in long_name:
        return long_name[5:]
    else:
        return long_name


def get_color_by_usage(usage: Meminfo) -> str:
    factor = usage.used / usage.total
    if factor > 0.8:
        return '\u001B[31m'  # red
    if factor > 0.7:
        return '\u001B[35m'  # orange
    if factor > 0.6:
        return '\u001B[33m'  # yellow
    if factor > 0.5:
        return '\u001B[36m'  # magenta
    if factor > 0.4:
        return '\u001B[34m'  # blue

    return '\u001B[32m'  # green


def draw_bar(factor: float, color: str, length: int) -> str:
    gray = '\u001B[1;30m'
    reset = '\u001B[0m'

    factor = max(0.0, min(1.0, factor))
    active = round(length * factor)
    inactive = length - active

    return '[' + color + '=' * active + gray + '=' * inactive + reset + ']'


def draw_resource_bar(factor: float) -> str:
    color = get_color_by_load(factor)
    length = round(get_term_width() / 8 + 4)

    return draw_bar(factor, color, length)


def draw_disk_bar(usage: Any) -> str:
    factor = usage.used / usage.total
    color = get_color_by_usage(usage)
    length = round(get_term_width() / 8 + 4)

    return draw_bar(factor, color, length)


def bytes_to_human(v: float) -> str:
    units = ['b', 'Kb', 'Mb', 'Gb', 'Tb', 'Pb']
    u = 0
    while v >= 1000:
        v /= 1000
        u += 1

    return "%.2f %s" % (v, units[u])


def format_disk_usage(usage: Any) -> str:
    color = get_color_by_usage(usage)
    reset = '\u001B[0m'

    used = bytes_to_human(usage.used)
    total = bytes_to_human(usage.total)

    return color + used + reset + ' / ' + total


def partitions_to_table(partitions: List[Partition]) -> List[List[str]]:
    table = []
    for partition in partitions:
        name = '\u001B[0m' + get_device_short_name(partition.device)
        try:
            raw_usage = shutil.disk_usage(partition.mountpoint)
            bar = draw_disk_bar(raw_usage)
            usage = format_disk_usage(raw_usage)
        except PermissionError:
            bar = '\u001B[31m?\u001B[0m'
            usage = '\u001B[31m?\u001B[0m'

        table.append([name, bar, usage])

    return table


def is_block_device_line(mount_line: str) -> bool:
    block_prefixes = [
        "/dev/block/",
        "/dev/sd",
        "/dev/nvme",
        "/dev/root",
        "/dev/mapper/",
    ]

    exclude_prefixes = [
        "/dev/block/bootdevice",
    ]

    for prefix in exclude_prefixes:
        if mount_line.startswith(prefix):
            return False

    for prefix in block_prefixes:
        if mount_line.startswith(prefix):
            return True

    return False


def get_mountpoints() -> List[Partition]:
    with open('/proc/mounts') as fh:
        rawmounts = filter(is_block_device_line, fh.readlines())

    result = []
    for [device, mountpoint, *_] in map(str.split, rawmounts):
        result.append(Partition(device=device, mountpoint=mountpoint))

    return result


def get_space_lines() -> List[List[str]]:
    partitions = get_mountpoints()
    return partitions_to_table(partitions)


def get_color_by_load(load: float) -> str:
    if load > 0.7:
        return '\u001B[31m'  # red
    if load > 0.6:
        return '\u001B[35m'  # orange
    if load > 0.5:
        return '\u001B[33m'  # yellow
    if load > 0.4:
        return '\u001B[36m'  # magenta
    if load > 0.3:
        return '\u001B[34m'  # blue

    return '\u001B[32m'  # green


def get_loadavg() -> float:
    with open('/proc/loadavg', 'r') as fh:
        averages = fh.read().split()
        return float(averages[0])


def get_cpu_count() -> int:
    with open('/proc/cpuinfo') as fh:
        return fh.read().count("processor")


def get_cpu_line() -> List[str]:
    try:
        cpu_load = get_loadavg() / get_cpu_count()
        color = get_color_by_load(cpu_load)

        bar = draw_resource_bar(cpu_load)
        val = color + '%.0f%%' % (cpu_load * 100) + '\u001B[0m'
    except PermissionError:
        bar = '?'
        val = '?'

    return ['cpu:', bar, val]


def get_meminfo() -> Meminfo:
    total = 0
    free = 0
    cached = 0
    with open('/proc/meminfo') as fh:
        for [key, value, *unit] in map(str.split, fh.readlines()):
            if key == 'MemTotal:':
                total = int(value) * 1024
            elif key == 'MemFree:':
                free = int(value) * 1024
            elif key == 'Cached:':
                cached = int(value) * 1024

    return Meminfo(
        total=total,
        free=free,
        cached=cached,
        used=total - free - cached
    )


def get_mem_line(title: str, key: Callable[[Meminfo], float]) -> List[str]:
    meminfo = get_meminfo()
    mem_load = key(meminfo) / meminfo.total
    color = get_color_by_load(mem_load)

    bar = draw_resource_bar(mem_load)
    val = color + bytes_to_human(key(meminfo)) + \
        '\u001B[0m / ' + bytes_to_human(meminfo.total)

    return [title + ':', bar, val]


def show_resources() -> None:
    table = get_space_lines()
    table.append(['', '', ''])
    table.append(get_cpu_line())
    table.append(get_mem_line("mem", lambda x: x.used))
    table.append(get_mem_line("mem+cached", lambda x: x.used + x.cached))

    print_table(table, ['RIGHT', 'LEFT', 'LEFT'])
    print()


def fin() -> None:
    print('\u001B[0m', end='')


show_banner()
show_uptime()
show_resources()
fin()
