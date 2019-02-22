import re
import pathlib
import requests
from urllib import parse
import argparse
from datetime import date


def parser():
    desc = 'Extract all 1a temp basal commands from Xcode logs and evaluate against PDM temp basals'
    parser = argparse.ArgumentParser(desc)
    parser.add_argument(
        'filename', type=str, help='filename to parse')
    parser.add_argument(
        'command_type', type=str, help='extra command to parse, for example bolus, basal, tempbasal')
    return parser


def get_raw_temp_basals_rtlomni(rtlomni_log_text):
    commands = []
    regex = r"(.*)\sID1.*BODY:([0-9A-Za-z]*).*\n.*\n.*CON:([A-Za-z0-9]+)*\s"
    select = re.findall(regex, rtlomni_log_text)
    for line in select:
        time = ' '.join(line[0][0:19].split('T'))
        string = "{}{}".format(line[1], line[2])
        raw_value = ''.join(map(str, string))
        commands.append({"time": time, "raw_value": raw_value})
    return commands


def get_raw_temp_basals_xcode(xcode_log_text, captureDate=date.today()):
    """
    Args:
        - xcode_log_text: raw xcode logs as a string
        - command: message type in lowercase, like:  '1a', '1f'
        - command_extra: message type in lowercase, like '13, '16', '17'
    Result:
        returns a list of all raw hex commands
    """
    commands = []
    key_name = r"Send\(Hex\)"

    key_name_present = re.findall(key_name, xcode_log_text)
    print(key_name_present)
    if key_name_present:
        regex = r"Send\(Hex\): .{0,12}(.*)\n([0-9-:\s]*)"
        select_1a_commands = re.findall(regex, xcode_log_text, re.MULTILINE)
        for line in select_1a_commands:
            commands.append({"time": line[1], "raw_value": line[0]})
            #print(line)
    else:
        regex = r"\* ([0-9-:\s]*)\s.*\s(send|receive)\s([a-z0-9]*)\n*"
        select_1a_commands = re.findall(regex, xcode_log_text, re.MULTILINE)
        for line in select_1a_commands:
            commands.append({"time": line[0], "raw_value": line[2][12:]})
            print(line)
    return commands


def parse_basal(line):
    raw_value = ''.join(map(str, raw_value))

    # 1a LL NNNNNNNN 00 CCCC HH SSSS PPPP napp napp napp 13 LL RR MM NNNN XXXXXXXX
    # 1a 12 b92270c2 00 06ba 29 10d8 0009 f01e f01e f01e 13 0e 40 00 0762 004c4b40

    command_elements = [
        line["time"],
        raw_value[0:2],    # 1a
        raw_value[2:4],    # LL
        raw_value[4:12],   # NNNNNNNN
        raw_value[12:14],  # 00
        raw_value[14:18],  # CCCC
        raw_value[18:20],  # HH
        raw_value[20:24],  # SSSS
        raw_value[24:28],  # PPPP
        raw_value[28:32],  # napp
        raw_value[32:36],  # napp
        raw_value[36:40],  # napp
        raw_value[40:44],  # napp
        raw_value[44:48],  # napp
        raw_value[48:50],  # 13
        raw_value[50:52],  # LL
        raw_value[52:54],  # RR
        raw_value[54:56],  # MM
        raw_value[56:60],  # NNNN
        raw_value[60:68],  # XXXXXXXX
        raw_value[68:72],  # YYYY
        raw_value[72:80],  # ZZZZZZZZ
        raw_value[80:84],  # YYYY
        raw_value[84:92],  # ZZZZZZZZ
        raw_value[92:96],  # YYYY
        raw_value[96:104],  # ZZZZZZZZ
        raw_value[104:108],  # YYYY
        raw_value[108:116]]  # ZZZZZZZZ
    command = ' '.join(command_elements)
    #print(command)
    return command


def parse_immediate_bolus(line):
    raw_value = line["raw_value"]

    #              1a LL NNNNNNNN 02 CCCC HH SSSS PPPP 0ppp 17 LL RR NNNN XXXXXXXX YYYY ZZZZZZZZ
    # 1f0bb35e0c1f 1a 0e 08f56c71 02 00b5 01 00a0 000a 000a 17 0d 00 0064 00030d40 0000 00000000 02f3

    if raw_value[38:42]:
        units = "{0:.2f}".format(int(raw_value[38:42], 16) * 0.05 / 10)
        if len(units) < 5:
            units = units.rjust(5)
    command_elements = [
        line["time"],
        units.zfill(5),
        raw_value[0:2],    # 1a
        raw_value[2:4],    # LL
        raw_value[4:12],   # NNNNNNNN
        raw_value[12:14],  # 02
        raw_value[14:18],  # CCCC
        raw_value[18:20],  # HH
        raw_value[20:24],  # SSSS
        raw_value[24:28],  # PPPP
        raw_value[28:32],  # 0app
        raw_value[32:34],  # 17
        raw_value[34:36],  # LL
        raw_value[36:38],  # RR
        raw_value[38:42],  # NNNN
        raw_value[42:50],  # XXXXXXXX
        raw_value[50:54],  # YYYY
        raw_value[54:62],  # ZZZZZZZZ
        ]
    command = ' '.join(command_elements)
    print(command)
    return command


def parse_temp_basal(line):
    raw_value = line["raw_value"]

    if raw_value[40:44]:
        units = "{0:.2f}".format(int(raw_value[40:44], 16)/100)
    else:
        units = ""
    command_elements = [
        #command_type,
        line["time"],
        "",
        units,
        " 0.5h",
        raw_value[0:2],
        raw_value[2:4],
        raw_value[4:12],
        raw_value[12:14],
        raw_value[14:18],
        raw_value[18:20],
        raw_value[20:24],
        raw_value[24:28],
        raw_value[28:32],
        raw_value[32:34],
        raw_value[34:36],
        raw_value[36:38],
        raw_value[38:40],
        raw_value[40:44],
        raw_value[44:52],
        raw_value[52:56],
        raw_value[56:64]]
    command = ' '.join(command_elements)
    #print(command)
    return command


def reformat_raw_hex(commands_list, command_type, captureDate=date.today()):
    print("List of commands:")
    commands = []
    if command_type == "bolus":
        print("Day        Time     Unit 1a LL NNNNNNNN 02 CCCC HH SSSS PPPP 0ppp 17 LL RR NNNN XXXXXXXX YYYY ZZZZZZZZ")
        for line in commands_list:
            raw_value = line["raw_value"]
            if raw_value[0:2] == '1a' and raw_value[32:34] == '17':
                command = parse_immediate_bolus(line)
            else:
                continue
            commands.append(command)
    if command_type == "tempbasal":
        print("Day        Time     1a LL NNNNNNNN 00 CCCC HH SSSS PPPP napp napp napp napp napp 13 LL RR MM NNNN XXXXXXXX YYYY ZZZZZZZZ YYYY ZZZZZZZZ YYYY ZZZZZZZZ")
        for line in commands_list:
            raw_value = line["raw_value"]
            #print(line)
            # if command_type == "basal" and raw_value[12:14] == '1a' and captureDate < date(2018, 11, 26):
            #    raw_value = ''.join(map(str, raw_value))
            if raw_value[0:2] == '1a' and raw_value[32:34] == '13':
                command = parse_basal(line)
            if raw_value[0:2] == '1a' and raw_value[32:34] == '16':
                command = parse_temp_basal(line)
            else:
                continue
            commands.append(command)
    return commands


def match_temp_basals_pdm(commands, command_type, rawgit_page_pdm_values):
    """
    Args:
        - commands: list of raw hex temp basal commands
        - filename_pdm_values: text file with a list of all temp basal values, spaced as on the openomni wiki
    Result:
        printed mismatched temp basals Loop vs PDM
    """
    output = {"total_results": '', "results": []}
    tested_results = []
    input_data_text = requests.get(rawgit_page_pdm_values).text
    temp_basals_pdm = re.search(r"```(.*)```", input_data_text, re.DOTALL)
    pdm_values = temp_basals_pdm.group(1).split('\n')
    mismatch = 0
    for i, command in enumerate(commands):
        for line in pdm_values:
            # print(line)
            # Replace reminders to 00 to match Loop
            if command_type == 'tempbasal':
                if line[59:61] != '00':
                    line = line[:59] + '00' + line[61:]
                unit_rate_loop = command[20:25].strip()  # command[12:18].strip()
                loop_command = command[47:].strip()
                pdm_command = line[27:].strip()

            if command_type == 'bolus':
                if line[53:55] != '00':
                    line = line[:53] + '00' + line[55:]
                unit_rate_loop = line[:5].strip()
                loop_command = command[40:].strip()
                # print(loop_command)
                pdm_command = line[20:].strip()
                # print(pdm_command)
            unit_rate_pdm = line[:5].strip()

            if unit_rate_loop == unit_rate_pdm:
                pre_name = "PDM................"
                pdm = pre_name + line
                # test after the nonce
                if loop_command == pdm_command:
                    match = "Yes"
                    break
                if loop_command != pdm_command:
                    match = "No"
            else:
                pdm = "This unit value does not match any of the PDM values."
                match = "No"
        tested_results.append({"pdm": pdm, "loop": command, "match": match})
        print(pdm)
        print(command)
        print(match)
        if match == "No":
                mismatch += 1
    if mismatch > 0:
        total_results = "Found {} mismatches".format(mismatch)

    else:
        total_results = "No {} mismatches found".format(command_type)
    print(total_results)
    return {"total_results": total_results, "results": tested_results, "header":  "Day....... Time.... "+ pdm_values[1]}


def extractor(file):
    wiki_url = 'https://raw.githubusercontent.com/wiki/openaps/openomni/'

    text = file.read().decode('utf-8')

    if pathlib.Path(file.name).suffix == '.omni':
        all_commands = get_raw_temp_basals_rtlomni(text)
    else:
        all_commands = get_raw_temp_basals_xcode(text)

    reports = []
    set_insulin_commands = [
        {"command_type": 'tempbasal', "wiki_page": 'All-Temp-basal-units-for-0.5h.md'},
        {"command_type": 'bolus', "wiki_page": 'All-Immediate-Bolus-Commands.md'}]
    for set_insulin_command in set_insulin_commands:
        pdm_values_url = parse.urljoin(wiki_url, set_insulin_command["wiki_page"])
        temp_basal_commands = reformat_raw_hex(all_commands, set_insulin_command["command_type"])
        matching_tempbasals = match_temp_basals_pdm(temp_basal_commands, set_insulin_command["command_type"], pdm_values_url)
        reports.append({"command_type": set_insulin_command["command_type"], "allcommands": temp_basal_commands, "matching_tempbasals": matching_tempbasals})

    print(reports)
    return reports


def main():
    args = parser().parse_args()
    with open(args.filename, 'rb') as input_file:
        output_json = extractor(input_file)


if __name__ == '__main__':
    main()
