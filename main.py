# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.

    with open(f"{directory}.507ex", 'wb') as f:
        f.write("FZX2".encode())
        f.write("\n!507EX-METADATA".encode())
        f.write(f"\n507ex-hash|{exec_hash}".encode())
        f.write(f"\n507ex-hashmode|blake2s".encode())
        f.write(f"\n507ex-id|{uuid.uuid4()}".encode())
        #DTOC - Date/Time of Creation
        f.write(f"\n507ex-dtoc|{datetime.now().now()}".encode())
        f.write(f"\n507ex-depends|{depend_file}".encode())
        f.write(f"\n!507EX-DEPENDENCIES\n{dependencies}".encode())
        f.write("\n!507EX-END-META\n".encode())
        f.write(exec_contents)
    print(f"Successfully built {directory}.507ex")

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
