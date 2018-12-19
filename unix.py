import stat
import pwd
import grp
import datetime
import time
import os

def get_unix_file_permissions_string(st, is_dir):
    # Check if directory or file
    if is_dir:
        pem_str = "d"
    else:
        pem_str = "-"

    # Get octal value of permissions of file
    pem = oct(stat.S_IMODE(st.st_mode))

    # Convert to binary
    b = bin(int(pem, 8))

    # Check if binary length is less than 11
    bit_length = b.__len__()
    if bit_length < 11:
        # Pad with zeroes on left side
        for i in range(bit_length, 11):
            b = b[:2] + "0" + b[2:]

    # Create array of read, write and execute flags
    pem_flags = ["r", "w", "x"]
    for bit in range(9):
        # If the current bit is 1, find and append the correct flag
        if b[bit + 2] == "1":
            pem_str += pem_flags[bit % 3]
        else:
            pem_str += "-"
    return pem_str


def get_last_changed_timestamp(changed_time):
    six_months_in_seconds = 15811200
    now = time.time()
    six_months_ago = now - six_months_in_seconds
    if changed_time < six_months_ago:
        return datetime.datetime.fromtimestamp(changed_time).strftime("%Y")
    return datetime.datetime.fromtimestamp(changed_time).strftime("%H:%M")


def get_unix_file_list_string(directory_path):
    directory = os.listdir(directory_path)
    file_list = ""
    for file in directory:
        # Absolute path
        file_path = directory_path + file

        # Get file status from operating system
        st = os.stat(file_path)

        # Is directory boolean
        is_dir = stat.S_ISDIR(st.st_mode)

        # Unix Permissions
        pem_string = get_unix_file_permissions_string(st, is_dir)

        # Real owner of file
        name = pwd.getpwuid(st.st_uid).pw_name

        # Real group of file
        group = grp.getgrgid(st.st_gid)[0]

        # Number of links to the inode, ST_NLINK is the 4th value of the 10-tuple returned by os.stat()
        link_count = st[3]

        # Size
        binary_size = st.st_size

        # Changed time in Unix time format
        changed_time = st[8]

        # Month when changed
        month_changed = datetime.datetime.fromtimestamp(changed_time).strftime("%b")

        # Day of month when changed
        day_of_month_changed = datetime.datetime.fromtimestamp(changed_time).strftime("%-d")

        # Either the clock as hour:minutes when last changed or the year, if more than six months ago
        timestamp = get_last_changed_timestamp(changed_time)

        file_list += ' '.join([pem_string, str(link_count), name, group, str(binary_size), month_changed,
                               day_of_month_changed, timestamp, file]) + "\r\n"
    return file_list
