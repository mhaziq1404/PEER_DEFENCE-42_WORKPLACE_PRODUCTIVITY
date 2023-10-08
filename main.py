

def make_graph(list: list):
    dict = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}
    for item in list:
        if (item['level'] >= 8):
            item['level'] = 8
        dict[int(item['level'])] += 1
    # plt.bar(dict.keys(), dict.values())
    # plt.xlabel('Cadets level')
    # plt.ylabel('Head counts')
    # plt.xticks([0, 1, 2, 3, 4, 5, 6, 7, 8])
    # plt.title('Selected cadets level distribution')
    # plt.savefig('bar_chart.png') 
    # # Display the plot
    # plt.close()
    return (dict)


# This is when the program is ran
print("\033[33m=========DHARMA GENERATOR========\033[0m     \033[31mby jakoh, bshamsid\033[0m")
print("\u001b[33mTo exit program type: 'exit'\033[0m")
print("\u001b[33mTo generate full list with updated users : 'full'\033[0m")
print("\u001b[33mTo update current list: 'update'\033[0m")
ipt = input("\033[0;35mCommand: \033[0m")
while ipt != "exit":
    if ipt == "full":
        get_all_users()
        filter_cadets()
        generate_sheet()
    elif ipt == "update":
        filter_cadets()
        generate_sheet()
    print("\u001b[33mTo exit program type: 'exit'\033[0m")
    print("\u001b[33mTo generate full list with updated users : 'full'\033[0m")
    print("\u001b[33mTo update current list: 'update'\033[0m")
    ipt = input("\033[0;35mCommand: \033[0m")