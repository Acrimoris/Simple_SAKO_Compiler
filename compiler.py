import os
import subprocess
import sys
import re
import argparse
from functools import reduce

def is_number(s):
    try:
        number = float(s)
    except ValueError:
        return ""
    if "." in s:
        return "float"
    else:
        return "int"

def process_math_operation(math_operation, user_functions=[]):
    global array_names
    # atan2 is not quite the same, but for me close enough (retunrs a value in range -pi to pi, while ARC returns 0<=ARC(X, Y)<=2pi)
    SAKO_functions = ["SIN", "COS", "TG", "ASN", "ACS", "ATG", "ARC", "PWK", "PWS", "LN", "EXP", "MAX", "MIN", "MOD", "SGN", "ABS", "ENT", "DIV", "SUM", "ILN", "ELM", "ADR"]
    C_functions = ["sin", "cos", "tan", "asin", "acos", "atan", "atan2", "sqrt", "cbrt", "log", "exp", "fmax", "fmin", "fmod", "sgn", "fabs", "(int)floor", "div", "sum", "iln", "elm", "&"]
    operations_list = "+-()/×⋄*"
    not_replace = SAKO_functions + user_functions
    # Replace '*' with '^'
    # Rest is lower, so it doesn't conflict with handle_square_brackets()
    math_operation = math_operation.replace('*', '^')
    math_operation = math_operation.replace("\n", "")
    # Change (x) in lists to [x]
    # Replace variables with four characters
    modified_operation = re.sub(r'\b([A-Z]+([0-9]*[A-Z]*)*)\b', lambda match: match.group(1)[:4], math_operation)

    # Replace round brackets with square brackets for list indexes
    modified_operation = re.sub(r'(\b[A-Z][A-Z0-9]*\b)\(([^)]+)\)', lambda match: f'{match.group(1)}[{match.group(2)}]' if match.group(1) not in not_replace else match.group(0), modified_operation)

    # Handle list indexes as math operations
    modified_operation = handle_square_brackets(modified_operation, not_replace, user_functions)

    # Handle "to the power of" operations, which aren't supported as good in C
    if "^" in modified_operation:
        if modified_operation.count("^") > 1:
            pattern = re.compile(r'(\w+|\w+\([^)]*\)|\w+\[[^\]]*\])\^(\w+)')
            while '^' in modified_operation:
                modified_operation = re.sub(pattern, r'pow(\1, \2)', modified_operation)
            t = []
            t2 = []
            for i in range(len(modified_operation)):
                if modified_operation[i] == ")" and i < len(modified_operation)-1 and modified_operation[i+1] == "(":
                    count = 1
                    t.append(i)
                    for z in range(i+2, len(modified_operation)):
                        if modified_operation[z] == "(":
                            count += 1
                        elif modified_operation[z] == ")":
                            count -= 1
                        if count == 0:
                            t2.append(z)
                            break
                if modified_operation[i] == ")" and i < len(modified_operation)-1 and modified_operation[i+1] == "[":
                    count = 1
                    t.append(i)
                    for z in range(i+2, len(modified_operation)):
                        if modified_operation[z] == "[":
                            count += 1
                        elif modified_operation[z] == "]":
                            count -= 1
                        if count == 0:
                            t2.append(z+1)
                            break
            for i in range(len(t)):
                if t[i] > t2[i]:
                    modified_operation = modified_operation[:t[i]] + modified_operation[t[i] + 1:]
                    modified_operation = modified_operation[:t2[i]] + ")" + modified_operation[t2[i]:]
                else:
                    modified_operation = modified_operation[:t2[i]] + ")" + modified_operation[t2[i]:]
                    modified_operation = modified_operation[:t[i]] + modified_operation[t[i] + 1:]
        else:
            operations_list="⋄*-+/"
            t = modified_operation.split("^")
            x = ""
            count = 0
            for i in reversed(t[0]):
                if str(i) == ")":
                    x += str(i)
                    count += 1
                    continue
                elif str(i) == "(":
                    count -= 1
                    x += str(i)
                    continue
                if str(i) not in operations_list:
                    x += str(i)
                else:
                    if count != 0:
                        x += str(i)
                    else:
                        break
            x = x[::-1]
            y = ""
            count = 0
            for i in t[1]:
                if i == "(":
                    count += 1
                    y += str(i)
                    continue
                elif i == ")":
                    count -= 1
                    y += str(i)
                    continue
                if i not in operations_list:
                    y += str(i)
                    continue
                elif count != 0:
                    y += str(i)
                    continue
            modified_operation = modified_operation.replace(f"{x}^{y}", f"pow({x},{y})")

    modified_operation = modified_operation if not any(sub in modified_operation for sub in SAKO_functions) else reduce(lambda s, pair: s.replace(pair[0], pair[1]), sorted(zip(SAKO_functions, C_functions), key=lambda x: len(x[0]), reverse=True), modified_operation)

    operations_list="⋄*-+/=[]>"
    for substring in array_names:
        if modified_operation == substring:
            modified_operation = f"*{modified_operation}"
            break
        index = modified_operation.find(substring)
        while index != -1:
            if index + len(substring) < len(modified_operation) and modified_operation[index + len(substring)] != '[' and modified_operation[index + len(substring)] in operations_list:
                modified_operation = modified_operation[:index] + '*' + modified_operation[index:]
            index = modified_operation.find(substring, index + 2)

    #print(modified_operation)
    modified_operation = modified_operation.replace('×', '*')
    modified_operation = modified_operation.replace('⋄', '*')
    return modified_operation

def handle_square_brackets(expression, not_replace, user_functions=[]):
    # Find all instances of array_name(...) within square brackets and process them recursively
    matches = re.findall(r'(\b[A-Za-z]+\b)\(([^)]+)\)', expression)
    for matching in matches:
        variable_name, subexpression = matching
        modified_subexpression = process_math_operation(subexpression, user_functions)
        if variable_name not in not_replace:
            expression = expression.replace(f'{variable_name}({subexpression})', f'{variable_name}[{modified_subexpression}]')
        else:
            expression = expression.replace(f'{variable_name}({subexpression})', f'{variable_name}({modified_subexpression})')

    square_bracket_matches = re.findall(r'\[([^]]+)\]', expression)
    count = 0
    result = ""
    for z in square_bracket_matches:
        count = 0
        result = ""
        for i in z:
            if i == "(":
                count += 1
                result += i
                continue
            if i == ")":
                count -= 1
                result += i
                continue
            if i == ",":
                if count == 0:
                    result += "]["
                else:
                    result += i
                continue
            result += i
        expression = expression.replace(f'{z}', f'{result}')
    return expression

def compile(input_file, output_file, encoding, keys):
    # Define global variables
    global loop_labels2
    global loops
    global array_names

    # Define basic variables
    integers = []
    array_names = []
    loop_labels = []
    used_variables = []
    user_functions = []
    loops_wol = 0
    last_label = "POCZ"

    # Add necessary C lines
    output_file.write("#include <stdio.h>\n#include <math.h>\n#include <stdlib.h>\n#include <string.h>\n#include <ctype.h>\n#include <unistd.h>\n\n")
    output_file.write("#define sum(X, Y, Z) _Generic((Z), int: ({ int sum = 0; for (int X = (Y); X > 0; X--) sum += (Z); sum; }), float: ({ float sum = 0; for (int X = (Y); X > 0; X--) sum += (Z); sum; }))\n")
    output_file.write("#define iln(X, Y, Z) _Generic((Z), int: ({ int iln = 1; for (int X = (Y); X > 0; X--) iln = iln * (Z); iln; }), float: ({ float iln = 1; for (int X = (Y); X > 0; X--) iln = iln * (Z); iln; }))\n")
    output_file.write("#define sgn(X, Y) (((sizeof(X) == sizeof(int)) ? abs(X) : fabsf(X)) * ((Y < 0) ? -1 : 1))\n")
    output_file.write("#define div(num, num2) (_Generic((num) / (num2), int: (int)((num) / (num2)), float: (int)floor((num) / (num2))))\n")
    output_file.write("#define elm(arr) ((int)(sizeof(arr) / sizeof(int)))\n\n")
    if encoding == "ASCII":
        output_file.write("int encoding[128] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110,111,112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127};\n")
    elif encoding == "Ferranti":
        output_file.write("int encoding[128] = {63, -1, 59, -1, -1, -1, -1, -1, -1, -1, 13, -1, -1, 30, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14, -1, -1, -1, 62, -1, -1, -1, 5, 6, 3, 26, 15, 11, 60, 23, 16, 1, 2, 19, -1, 21, 22, 7, 8, 25, 18, -1, -1, 10, 17, 61, -1, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, -1, -1, 9, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,-1, -1, -1, -1, -1,-1, -1, -1, -1, 20, -1, 24, -1};\n")
    else:
        output_file.write("int encoding[128] = {61, -1, -1, -1, -1, -1, -1, -1, -1, -1, 58, -1, 60, 62, 20, 47, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 19, -1, -1, -1, -1, 1, -1, -1, -1, -1, -1, -1, 12, 3, 6, 5, 4, 10, 8, 2, 9, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 11, 7, 16, 13, 17, 18, -1, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 14, -1, 15, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 59, 63};\n")
    output_file.write(f"int keys[] = {keys}; int opt;\n")
    output_file.write("int main(int argc, char *argv[]) {\n")
    output_file.write("    char input[120];\n")
    # Oneliner for getting keys
    output_file.write("    while ((opt = getopt(argc, argv, \"k:\")) != -1) { if (opt == 'k') { char *token = strtok(optarg, \",\"); while (token != NULL) { int index = atoi(token); if (index >= 0 && index < 35) { keys[index] = 1; } token = strtok(NULL, \",\"); } } }\n")

    # Define regexes patterns
    match_labels = r"^\s*\**[0-9]+[A-Z]*([0-9]*[A-Z]*)*\)"
    match_gotos = r"^\s*SKOCZ\s*DO\s*"

    # Define boolean variables
    jezyk_SAS = False
    inside_TEKST = False
    inside_TABLICA = False

    moved_List_B = False
    moved_List_CZ = False
    moved_List_DR = False
    moved_List_DRW = False
    moved_List_CZW = False

    zline_zindex = 18
    error_line_index = 0
    for line in input_file:
        # Add one to index
        zline_zindex += 1
        error_line_index += 1
        # Make line case insensitive
        line = line.upper()
        # Debug lines
        #if line.replace("\n", "").replace(" ", "") != "": print(line.replace("\n", ""), zline_zindex)
        # print(integers)
        # Check for SAKO keywords
        # "start" stays, as I started with this keyword
        start = line.replace(" ", "").replace("\n", "").replace(":", "").find("TEKST")
        calkowite_c = line.replace(" ", "").find("CALKOWITE:")
        decimal_operation_c = line.replace(" ", "").find("=")
        octal_and_binary_operation_c = line.replace(" ", "").find("[")
        stop = line.replace(" ", "").find("STOP")
        koniec = line.replace(" ", "").find("KONIEC")
        jump_to = re.match(match_gotos, line)
        comment_c = line.replace(" ", "").find("K)") if line.replace(" ", "").find("K)") != -1 else line.replace(" ", "").find(":")
        spaces = line.replace(" ", "").find("SPACJA") if line.replace(" ", "").find("SPACJA") != -1 else line.replace(" ", "").find("SPACJI")
        newlines = line.replace(" ", "").find("LINIA") if line.replace(" ", "").find("LINIA") != -1 else line.replace(" ", "").find("LINII")
        gdy_c = line.replace(" ", "").find("GDY")
        gdy_inaczej_c = line.replace(" ", "").find("INACZEJ")
        drukuj_c = line.replace(" ", "").find("DRUKUJ(")
        blok_c = line.replace(" ", "").find("BLOK")
        tablica_c = line.replace(" ", "").find("TABLICA")
        label_c = re.match(match_labels, line) or re.match(r"^\**\)", line)
        czytaj = line.replace(" ", "").find("CZYTAJ:")
        loop_c = line.replace(" ", "").find("POWTORZ")
        skocz_wedlug = line.replace(" ", "").find("SKOCZWEDLUG")
        drukuj_wiersz = line.replace(" ", "").find("DRUKUJWIERSZ:")
        czytaj_wiersz = line.replace(" ", "").find("CZYTAJWIERSZ:")
        strona_c = line.replace(" ", "").replace("\n", "") == "STRONA"
        beben_pisz_c = line.replace(" ", "").startswith("PISZNABEBENOD")
        beben_czytaj_c = line.replace(" ", "").startswith("CZYTAJZBEBNAOD")

        ###############
        # Empty Lines #
        ###############
        if line.replace(" ", "").replace("\n","") == "" and inside_TEKST == False and not inside_TABLICA:
            zline_zindex -= 1
            error_line_index -= 1
            continue
        if line.replace(" ", "").replace("\n","").find("STRUKTURA") != -1 and inside_TEKST == False and not inside_TABLICA and not line.strip().startswith("K)") and not line.strip().startswith(":"):
            zline_zindex -= 1
            error_line_index -= 1
            continue

        ############
        # COMMENTS #
        ############
        if comment_c != -1 and inside_TEKST == False and not inside_TABLICA:
            line = line.replace(" ", "")
            if line.startswith("K)"):
                zline_zindex -= 1
                continue
            elif line.startswith(":"):
                zline_zindex -= 1
                continue
        if (line.replace(" ", "").startswith("USTAWSKALE") or line.replace(" ", "").startswith("ZWIEKSZSKALE") or line.replace(" ", "").startswith("SKALA") or line.replace(" ", "").replace("\n","") == "KONIECROZDZIALU") and not inside_TABLICA and not inside_TEKST:
            zline_zindex -= 1
            continue
        if ";" in line:
            return "Semicolon", error_line_index + 1, last_label

        ###############
        # Moved lists #
        ###############
        if "-" in integers:
            line = line.replace(" ", "").replace("\n", "").split(",")
            integers.remove("-")
            integers.extend(line)
            zline_zindex -= 1
            continue
        if moved_List_B:
            line = line.replace(" ", "").replace("\n", "").split(",")
            for z, i in enumerate(line):
                if i != "-":
                    is_float = "float" * (f"*{i}" not in integers) + "int" * (f"*{i}" in integers)
                    used_variables.append(i)
                    output_file.write(f"    {is_float} {i}[{int(line[0])+1}];\n")
                    moved_List_B = False
                    if z != 0:
                        zline_zindex += 1
                else:
                    moved_List_B = True
                    break
            continue
        if moved_List_DR:
            t = line.replace(" ", "").replace("\n", "").split(",")
            line = line_DR
            for i in t:
                i = process_math_operation(i)
                t2 = re.sub(r'\[.*?\]', '', i)
                if i == "-":
                    moved_List_DR = True
                    line = "$"
                    break
                if i.isdigit():
                    is_float = "f" * ("." in i) + "d" * ("." not in i)
                else:
                    is_float = "f" * (f"{i}" not in integers and f"*{t2}" not in integers) + "d" * (f"{i}" in integers or f"*{t2}" in integers)
                output_file.write("    if (" + i + " >= 0) {\n")
                output_file.write(f"        printf(\" %{line}{is_float}\", {i});\n")
                output_file.write("    } else {\n")
                if "." in line[0]:
                    output_file.write(f"        printf(\"%{line}+1{is_float}\", {i});\n")
                else:
                    output_file.write(f"        printf(\"%{line}+1{is_float}\", {i});\n")
                output_file.write("    }\n")
                zline_zindex += 5
            zline_zindex -= 1
            if line != "$":
                moved_List_DR = False
            continue
        if moved_List_CZW:
            line = line.replace(" ", "").replace("\n", "").split(",")
            for i in line:
                if f"*{i}" not in integers:
                    break
                if i == "-":
                    moved_List_CZW = True
                    line = "$"
                    break
                output_file.write(f"    fgets(input, sizeof(input), stdin);\n")
                zline_zindex += 1
                output_file.write("    for (int i = 0; i < strlen(input); ++i) {\n")
                if encoding != "ASCII":
                    output_file.write(f"       {i}[i] = encoding[(int)input[i]];\n")
                else:
                    output_file.write(f"        {i}[i] = input[i];\n")
                output_file.write("    }\n")
                zline_zindex += 3
            zline_zindex -= 1
            if line != "$":
                moved_List_CZW = False
            continue
        if moved_List_DRW:
            line = line.replace(" ", "").replace("\n", "").split(",")
            for i in line:
                if f"*{i}" not in integers:
                    break
                if i == "-":
                    moved_List_CZW = True
                    line = "$"
                    break
                output_file.write("    for (int i = 0; i < elm("+i+"); ++i) {\n")
                output_file.write("        for (int j = 0; j < 128; ++j) {\n")
                output_file.write("            if (encoding[j] == "+i+"[i]) {\n")
                output_file.write("                printf(\"%c\", (char)j);\n")
                output_file.write("                break;\n")
                output_file.write("            }\n")
                output_file.write("        }\n")
                output_file.write("    }\n")
                zline_zindex += 8
            zline_zindex -= 1
            if line != "$":
                moved_List_DRW = False
            continue

        ##########
        # LABELS #
        ##########
        if label_c:
            # TODO: Support weird loop notation, like "1A) *** *)*", or "*)*"
            t = re.search(match_labels, line) or re.search(r"^\**\)", line)
            t = t.group(0).replace(")", "")
            t2 = t.replace("*", "")
            t2 = t2[:4]
            if t2 != "":
                output_file.write(f"    _{t2}:\n")
                last_label = t2
                error_line_index = -1
            else:
                #output_file.write(f"    LX{loops_wol}:\n")
                t = "*" * t.count("*") + f"LX{loops_wol}"
                loops_wol += 1
                zline_zindex -= 1
            for _ in range(t.count("*")):
                loop_labels.append([f"LS{loops}", zline_zindex+1])
                loops += 1
                loop_labels2.append([t.replace("*", "")[:4], zline_zindex+1])
            line = re.sub(match_labels, '', line)
            if re.search(r"^\**\)", line): line = re.sub(r"^\**\)", '', line)
            zline_zindex += 1

        ############################
        # JEZYK SAS and JEZYK SAKO #
        ############################
        if line.replace(" ", "").replace("\n","") == "JEZYKSAS" and inside_TEKST == False and not inside_TABLICA:
            jezyk_SAS = True
            output_file.write("    asm(")
        elif line.replace(" ", "").replace("\n","") == "JEZYKSAKO" and jezyk_SAS:
            jezyk_SAS = False
            output_file.write("    );\n")
        elif line.replace(" ", "").replace("\n","") == "JEZYKSAKO" and not jezyk_SAS:
            return 29
        elif jezyk_SAS:
            output_file.write(f'        {line}')

        #########
        # TEKST #
        #########
        if start != -1 and line.find("WIERSZY") == -1 and not inside_TABLICA:
            tek_wie = -1
            inside_TEKST = True
            start += len("TEKST")

            # Skip spaces
            while start < len(line) and line[start].isspace():
                start += 1

            # Check for optional colon
            if start < len(line) and line[start] == ':':
                start += 1
                # Skip spaces after colon
                while start < len(line) and line[start].isspace():
                    start += 1

            # Remove the last symbol from start
            start = start if len(line) <= start else start - 1
            line = line[:start] + line[start+1:]
            zline_zindex -= 1
            continue
        elif inside_TEKST:
            tek_wie -= 1
            tek_wie2 = True
            if tek_wie > 0:
                line = line.replace("\n", "\\n")
                output_file.write(f'    printf("{line}");\n')
            else:
                inside_TEKST = False
                if tek_wie2 == True:
                    line = line.replace("\n", "\\n")
                    tek_wie2 = False
                else:
                    line = line.replace("\n", "")
                output_file.write(f'    printf("{line}");\n')
            continue
        elif start != -1 and line.find("WIERSZY") != -1 and not inside_TABLICA:
            tek_wie2 = False
            tek_wie = 0
            line = line.replace(" ", "").replace("TEKST", "").replace("\n", "").replace("WIERSZY", "").replace(":", "")
            tek_wie = int(eval(line.replace("*", "**").replace("×", "*").replace('⋄', '*')))
            inside_TEKST = True
            zline_zindex -= 1
            continue

        #########
        # GOTOS #
        #########
        if jump_to and not inside_TABLICA:
            line = line.replace(" ", "").replace("\n", "").replace("SKOCZDO", "").replace(":", "")[:4]
            if line != "NASTEPNY":
                output_file.write(f"    goto _{line};\n")
            else:
                zline_zindex -= 1
            continue

        ##########################
        # GOTOS ACCORDINGLY TO X #
        ##########################
        if skocz_wedlug != -1 and not inside_TABLICA:
            line = line.replace(" ", "").replace("\n", "").replace("SKOCZWEDLUG", "").split(":")
            t = line[1].split(",")
            variable = line[0].replace("(", "").replace(")", "")
            output_file.write("    switch (" + variable + ") {\n")
            for i, z in enumerate(t):
                output_file.write(f"        case {i}:\n")
                if z == "NASTEPNY":
                    output_file.write(f"            break; //goto _NASTEPNY;\n")
                else:
                    output_file.write(f"            goto _{t[i][:4]};\n")
            output_file.write("    }\n")
            zline_zindex += (len(t)*2) + 1
            continue


        #########
        # LOOPS #
        #########
        if loop_c != -1 and not inside_TABLICA:
            line = line.replace("\n", "").replace(" ", "")
            label1 = loop_labels[len(loop_labels)-1][0]
            line = line.split(":")[1]
            variable = line.split("=")[0]
            line = line.split("=")[1]
            operations_list = ["+", "-", "/", "×", "*"]
            count = 0
            t = []
            t2 = []
            for z, i in enumerate(line):
                if i == "(":
                    count += 1
                elif i == ")":
                    count -= 1
                    if count == 0:
                        t.append(z)
            for i in reversed(t):
                if i < len(line) - 1 and line[i+1] not in operations_list:
                    t2.append(line[:i])
                    t2.append(line[i:])
            line = t2[0]
            end = t2[1][1:]
            count = 0
            t = []
            for z, i in reversed(list(enumerate(line))):
                if i == "(":
                    count -= 1
                    if count < 0:
                        t.append(z)
                elif i == ")":
                    count += 1
            start_loop = line[:t[0]]
            step = line[t[0]+1:]

            start_loop = process_math_operation(start_loop)
            step = process_math_operation(step)
            end = process_math_operation(end)

            # print(variable, start_loop, step, end)
            used =  "float" * ((variable not in integers) and (variable not in used_variables)) + "int" * (variable not in used_variables) * (variable in integers)
            if len(loop_labels2[len(loop_labels2)-1]) != 3:
                loop_labels2[len(loop_labels2)-1].append(f"    {used} {variable} = {start_loop};\n")
            else:
                for i in reversed(loop_labels2):
                    if len(i) != 3:
                        i.append(f"    {used} {variable} = {start_loop};\n")
                        break
            # print(loop_labels2)
            if variable not in used_variables: used_variables.append(variable)
            if variable in integers:
                output_file.write("    if (" + str(variable) + " != " + str(end) + ") {\n")
                output_file.write(f"        {variable} = {variable} + {step};\n")
                output_file.write(f"        goto {label1};\n")
                output_file.write("    }\n")
                zline_zindex += 3
            else:
                output_file.write("    if (fabs(" + str(step) + "/2.0) <= fabs(" + str(variable)  + "-" + str(end) + ")) {\n")
                output_file.write(f"        {variable} = {variable} + {step};\n")
                output_file.write(f"        goto {label1};\n")
                output_file.write("    }\n")
                zline_zindex += 3
            del loop_labels[len(loop_labels)-1]
            continue

        #############
        # CALKOWITE #
        #############
        if calkowite_c != -1 and not inside_TABLICA:
            calkowite_c += len("CALKOWITE:")

            # Skip spaces
            while calkowite_c < len(line) and line[calkowite_c].isspace():
                calkowite_c += 1

            # Remove the \n symbol
            line = line[:-1] if len(line) > 1 else line

            # Extract values after "CALKOWITE:"
            values = line.split(":")[1].replace(" ", "").split(",")
            for z, i in enumerate(values):
                if "*" not in i:
                    i = i[:4]
                else:
                    i = "*" + i.replace("*", "")[:4]
                values[z] = i
            integers.extend(values)
            zline_zindex -= 1
            continue

        ########################
        # Variables Definition #
        ########################
        if decimal_operation_c != -1 and gdy_c == -1 and loop_c == -1 and inside_TABLICA == False:
            count = 0
            for i in line:
                if i == "(":
                    count += 1
                elif i == ")":
                    count -= 1
                if i == "=" and count != 0:
                    count = True
                    break
            if count == True:
                line = line.replace(" ", "")
                line = process_math_operation(line)
                z = line.split("=")
                z = z[len(z)-1]
                vart = line.split("[")[0]
                line = line.replace(f"{vart}", "").replace(f"={z}", "")
                t = []
                t2 = ""
                count = 0
                for index, i in enumerate(line):
                    if i == "[":
                        count += 1
                        t2 += i
                    elif i == "]":
                        count -= 1
                        t2 += i
                    else:
                        t2 += i
                    if i == "]" and count == 0 and index != 0:
                        t2 = t2[1:len(t2)-1]
                        t.append(t2)
                        t2 = ""
                line = t

                t = []
                for index, i in enumerate(line):
                    if "=" in i:
                        i = i.replace("=", "")
                        line[index] = i
                        if i not in t: t.append(i)

                count = 0
                count2 = 0
                t3 = []
                for i in line:
                    if i in t and i not in t3:
                        indent = "    " * (count + 1)
                        r = "[0]" * (count2)
                        r2 = "[0]" * (count2 + 1)
                        used = "int " * (i not in used_variables)
                        output_file.write(f"{indent}for ({used}{i} = 0; {i} < sizeof({vart}{r})/sizeof({vart}{r2}); {i}++) {{\n")
                        count += 1
                        t3.append(i)
                        zline_zindex += 1
                    count2 += 1

                for i in line:
                    vart += f"[{i}]"

                indent = "    " * (count + 1)
                output_file.write(f"{indent}{vart} = {z};\n")

                for i in range(count):
                    indent = "    " * (count)
                    output_file.write(indent + "}\n")
                    count -= 1
                    zline_zindex += 1
                continue

            if len(line) >= 3 and count != True:
                is_float = ""
                whole = line.replace(" ", "").split("=")
                variable = whole[0]
                variable = process_math_operation(variable)
                operation = whole[1]
                operation = process_math_operation(operation, user_functions)
                vart = re.sub(r'\[.*?\]', '', variable)[:4]
                if variable[0] != "*":
                    is_float = "float" * ((variable not in integers) and (f"*{vart}" not in integers) and (variable not in used_variables) and (vart not in used_variables)) + "int" * ((variable not in used_variables) and (vart not in used_variables)) * ((variable in integers) or (f"*{vart}" in integers))
                    if variable not in used_variables and vart not in used_variables: used_variables.append(vart)
                output_file.write(f"    {is_float} {variable} = {operation};\n")
                continue

        ###################
        # List Definition #
        ###################
        if blok_c != -1 and not inside_TABLICA:
            t = []
            t2 = ""
            line = line.replace(" ", "").replace("\n", "").replace("BLOK(", "").replace(")", "").split(":")
            values = line[1].split(",")
            line = line[0]
            line = line.split(",")
            for i in line:
                i = str(eval(str(i.replace("*", "**").replace("×", "*").replace('⋄', '*')) + "+1"))
                t.append(f"[{i}]")
            line = ""
            for i in t:
                line += i
            for z, i in enumerate(values):
                i = i[:4]
                if i != "-":
                    is_float = "float" * (f"*{i}" not in integers) + "int" * (f"*{i}" in integers)
                    used_variables.append(i)
                    output_file.write(f"    {is_float} {i}{line};\n")
                    array_names.append(i)
                    if z != 0:
                        zline_zindex += 1
                else:
                    moved_List_B = True
                    break
            continue

        ###########
        # TABLICA #
        ###########
        if tablica_c != -1:
            line = line.replace(" ", "").replace("\n", "").replace("TABLICA(", "").replace(")", "").split(":")
            TABLICA_numbers = line[0].split(",")
            for i in range(len(TABLICA_numbers)):
                TABLICA_numbers[i] = int(eval((TABLICA_numbers[i]+"+1").replace("*", "**").replace("×", "*").replace('⋄', '*')))
            TABLICA_name = line[1][:4]
            t = ""
            used_variables.append(TABLICA_name)
            array_names.append(TABLICA_name)
            inside_TABLICA = True
            zline_zindex -= 1
            continue
        elif inside_TABLICA and line.replace(" ", "").replace("\n", "") != "*":
            try:
                t2 = ""
                length = len(line)
                i = 0
                while i < length:
                    t2 += line[i]
                    if line[i] == '+' or line[i] == '-':
                        i += 1
                        while i < length and line[i] == ' ':
                            i += 1
                        while i < length and line[i].isdigit():
                            t2 += line[i]
                            i += 1
                        i -= 1
                    i += 1
                line = t2
                if "=" in line or ":" in line:
                    t2 = 0
                    for z, i in enumerate(line):
                        if i == "=" or i == ":":
                            t2 = z + 1
                            break
                    t += f" {line[t2:]}"
                else:
                    t += line
                zline_zindex -= 1
                continue
            except Error as e:
                return 3, error_line_index + 1, last_label
        elif inside_TABLICA and line.replace(" ", "").replace("\n", "") == "*":
            if f"*{TABLICA_name}" in integers:
                numbers_list = list(map(int, t.split()))
                is_float = "int"
            else:
                numbers_list = list(map(float, t.split()))
                is_float = "float"
            # Determine the shape of the multidimensional array based on the given numbers
            shape = list(map(int, TABLICA_numbers[::-1]))
            # Create the multidimensional array using list comprehension
            result = [numbers_list[i:i + shape[0]] for i in range(0, len(numbers_list), shape[0])]
            for dim in shape[1:]:
                result = [result[i:i + dim] for i in range(0, len(result), dim)]
            result = str(result)[1:-1].replace("[", "{").replace("]", "}")
            TABLICA_numbers = str(TABLICA_numbers).replace(",", "][")
            output_file.write(f"    {is_float} {TABLICA_name}{TABLICA_numbers} = {result};\n")
            inside_TABLICA = False
            continue

        ##########
        # SPACES #
        ##########
        if spaces != -1:
            spaces = False
            line = line.replace(" ", "").replace("\n", "").replace(":", "")
            line = line.replace("SPACJA", "").replace("SPACJI", "")
            if line != "":
                spaces = True
            if spaces == True:
                t = process_math_operation(line)
                output_file.write("    for (int i = 0; i < " + t +"; i++) {\n")
                output_file.write("        printf(\" \");\n")
                output_file.write("    }\n")
                zline_zindex += 2
            else:
                output_file.write("    printf(\" \");\n")
            continue

        ############
        # NEWLINES #
        ############
        if newlines != -1:
            newlines = False
            line = line.replace(" ", "").replace(":", "").replace("\n", "").replace("LINIA", "").replace("LINII", "")
            if line != "":
                newlines = True
            if newlines == True:
                t = process_math_operation(line)
                output_file.write("    for (int i = 0; i < " + str(t) +"; i++) {\n")
                output_file.write("        printf(\"\\n\");\n")
                output_file.write("    }\n")
                zline_zindex += 2
            else:
                output_file.write("    printf(\"\\n\");\n")
            continue

        ##########
        # STRONA #
        ##########
        if strona_c:
            output_file.write("    printf(\"\");\n")
            continue

        ######################
        # PRINTING VARIABLES #
        ######################
        if drukuj_c != -1:
            # TODO: Make DRUKUJ numbers more accurate to SAKO (especially real numbers)
            if line.replace(" ", "").replace("\n", "")[-1] == "-":
                moved_List_DR = True
            line = line.replace(" ", "").replace("\n", "").replace("DRUKUJ(", "").replace("):", ":").split(":")
            t = line[1]
            pattern_DRUKUJ = re.compile(r'\b(?:[A-Z]+\(\S*\)|\d+\.\d+|\w+\([^\)]*\)|\w+)')
            t = pattern_DRUKUJ.findall(t)
            # print(t)
            line = line[0].replace(",", ".")
            if line.count(".") > 1:
                line = line[:line[0].rfind(".")].split(".")
                line[0] = process_math_operation(line[0])
                line[1] = process_math_operation(line[1])
                line = str(line[0]) + str(line[1])
            else:
                line = process_math_operation(line)
            if moved_List_DR:
                line_DR = line
            for i in t:
                i = process_math_operation(i)
                t2 = re.sub(r'\[.*?\]', '', i)
                if i.isdigit():
                    is_float = "f" * ("." in i) + "d" * ("." not in i)
                else:
                    is_float = "f" * (f"{i}" not in integers and f"*{t2}" not in integers) + "d" * (f"{i}" in integers or f"*{t2}" in integers)
                output_file.write("    if (" + i + " >= 0) {\n")
                output_file.write(f"        printf(\" %{line}{is_float}\", {i});\n")
                output_file.write("    } else {\n")
                if "." in line[0]:
                    output_file.write(f"        printf(\"%{line}{is_float}\", {i});\n")
                else:
                    output_file.write(f"        printf(\"%{line}{is_float}\", {i});\n")
                output_file.write("    }\n")
                zline_zindex += 5
            zline_zindex -= 1
            continue

        ##########
        # CZYTAJ #
        ##########
        if czytaj != -1:
            line = line.replace(" ", "").replace("\n", "").replace("CZYTAJ:", "").split(",")
            if line[len(line)-1] == "-":
                moved_List_CZ = True
                line.pop()
            t = line[0].replace("*", "")
            for z, i in enumerate(line):
                vart = re.sub(r'\[.*?\]', '', i)
                if "*" in i:
                    is_float = "f" * ((i not in integers) and (f"*{vart}" not in integers)) + "i" * ((i in integers) or (f"*{vart}" in integers))
                    is_float2 = "float" * ((i not in integers) and (f"*{vart}" not in integers)) + "int" * ((i in integers) or (f"*{vart}" in integers))
                    ptr = f"{is_float2}* ptr{is_float}" if f"ptr{is_float}" not in used_variables else f"ptr{is_float}"
                    if f"ptr{is_float}" not in used_variables: used_variables.append(f"ptr{is_float}")
                    i = i.replace("*", "")
                    output_file.write(f"    {ptr} = (void*){i};\n")
                    output_file.write("    while (1) {\n")
                    output_file.write("        if (fgets(input, sizeof(input), stdin) == NULL) {\n")
                    output_file.write("            break;\n")
                    output_file.write("        }\n")
                    output_file.write("        char* trimmedInput = input;\n")
                    output_file.write("        while (*trimmedInput == ' ') {\n")
                    output_file.write("            trimmedInput++;\n")
                    output_file.write("        }\n")
                    output_file.write("        if (*trimmedInput == '*') {\n")
                    output_file.write("            break;\n")
                    output_file.write("        }\n")
                    output_file.write("        if (isdigit(*trimmedInput) || *trimmedInput == '+' || *trimmedInput == '-') {\n")
                    output_file.write("            char* token = strtok(trimmedInput, \" \\n\");\n")
                    output_file.write("            while (token != NULL) {\n")
                    output_file.write(f"                *ptr{is_float} = ato{is_float}(token);\n")
                    output_file.write(f"                ptr{is_float}++;\n")
                    output_file.write("                token = strtok(NULL, \" \\n\");\n")
                    output_file.write("            }\n")
                    output_file.write("        } else {\n")
                    output_file.write("            char* delimiter = strpbrk(trimmedInput, \":=\");\n")
                    output_file.write("            if (delimiter != NULL) {\n")
                    output_file.write("                trimmedInput = delimiter + 1;\n")
                    output_file.write("            }\n")
                    output_file.write("            char* token = strtok(trimmedInput, \" \\n\");\n")
                    output_file.write("            while (token != NULL) {\n")
                    output_file.write(f"                *ptr{is_float} = ato{is_float}(token);\n")
                    output_file.write(f"                ptr{is_float}++;\n")
                    output_file.write("                token = strtok(NULL, \" \\n\");\n")
                    output_file.write("            }\n")
                    output_file.write("        }\n")
                    output_file.write("    }\n")
                    zline_zindex += 32
                else:
                    is_float = "float" * ((i not in integers) and (f"*{vart}" not in integers) and (i not in used_variables) and (vart not in used_variables)) + "int" * ((i not in used_variables) and (vart not in used_variables)) * ((i in integers) or (f"*{vart}" in integers))
                    is_float2 = "f" * ("float" in is_float) + "i" * ("int" in is_float)
                    output_file.write(f"    {is_float} {i};\n")
                    output_file.write("    fgets(input, sizeof(input), stdin);\n")
                    output_file.write(f"    char* spacePtr = strchr(input, ' ');\n")
                    output_file.write("    while (spacePtr) {\n")
                    output_file.write("        memmove(spacePtr, spacePtr + 1, strlen(spacePtr));\n")
                    output_file.write(f"        spacePtr = strchr(input, ' ');\n")
                    output_file.write("    }\n")
                    output_file.write("    if (isdigit(input[0]) || input[0] == '+' || input[0] == '-') {\n")
                    output_file.write(f"        {i} = ato{is_float2}(input);\n")
                    output_file.write("    } else {\n")
                    output_file.write("         char *ptr = strchr(input, ':');\n")
                    output_file.write("         if (!ptr) ptr = strchr(input, '=');\n")
                    output_file.write("         if (ptr) {\n")
                    output_file.write("             memmove(input, ptr + 1, strlen(ptr));\n")
                    output_file.write(f"             {i} = ato{is_float2}(input);\n")
                    output_file.write("         }\n")
                    output_file.write("    }\n")
                    zline_zindex += 17
            zline_zindex -= 1
            continue

        #################
        # CZYTAJ WIERSZ #
        #################
        if czytaj_wiersz != -1:
            line = line.replace(" ", "").replace("\n", "").replace("CZYTAJWIERSZ:", "").split(",")
            for i in line:
                if f"*{i}" not in integers:
                    break
                if i == "-":
                    moved_List_CZW = True
                    break
                output_file.write(f"    fgets(input, sizeof(input), stdin);\n")
                output_file.write("    for (int i = 0; i < strlen(input); ++i) {\n")
                if encoding != "ASCII":
                    output_file.write(f"       {i}[i] = encoding[(int)input[i]];\n")
                else:
                    output_file.write(f"        {i}[i] = input[i];\n")
                output_file.write("    }\n")
                zline_zindex += 4
            zline_zindex -= 1
            continue

        #################
        # DRUKUJ WIERSZ #
        #################
        if drukuj_wiersz != -1:
            line = line.replace(" ", "").replace("\n", "").replace("DRUKUJWIERSZ", "").replace(":", "").split(",")
            for i in line:
                if i == "-":
                    moved_List_DRW = True
                    break
                if f"*{i}" not in integers:
                    break
                output_file.write("    for (int i = 0; i < elm("+i+"); ++i) {\n")
                output_file.write("         for (int j = 0; j < 128; ++j) {\n")
                output_file.write("             if (encoding[j] == "+i+"[i]) {\n")
                output_file.write("                 printf(\"%c\", (char)j);\n")
                output_file.write("                 break;\n")
                output_file.write("             }\n")
                output_file.write("         }\n")
                output_file.write("    }\n")
                zline_zindex += 8
            zline_zindex -= 1
            continue

        #######################
        # IF AND KEYS SUPPORT #
        #######################
        if gdy_c != -1 and gdy_inaczej_c != -1:
            if line.replace(" ", "").startswith("GDYKLUCZ"):
                line = line.replace(" ", "").replace("\n", "").split(",INACZEJ")
                t, t2 = "", ""
                label2 = line[1]
                line = line[0]
                line = line.split(":")
                label1 = line[1]
                line = line[0].replace("GDYKLUCZ", "")
                line = process_math_operation(line)
                if label1 == "NASTEPNY":
                    t = "//"
                if label2 == "NASTEPNY":
                    t2 = "//"
                label1, label2 = label1[:4], label2[:4]
                line = f"keys[{line}] == 1"
                output_file.write("    if (" + line + ") {\n")
                output_file.write(f"        {t}goto _{label1};\n")
                output_file.write("    } else {\n")
                output_file.write(f"        {t2}goto _{label2};\n")
                output_file.write("    }\n")
                zline_zindex += 4
                continue

            if line.replace(" ", "").startswith("GDYBYLNADMIAR"):
                line = line.replace(" ", "").replace("\n", "").split(",INACZEJ")
                label2 = line[1]
                label2 = label2[:4]
                line = line[0]
                line.replace("GDYBYLNADMIAR:", "")
                label1 = line[:4]
                t = "//" * (label2 == "NAST")
                # There is no detection for that right now, so it's just goto
                output_file.write(f"    {t}goto _{label2};\n")
                continue

            t, t2, mode = "", "", ""
            line = line.replace(" ", "").replace("\n", "").split(",INACZEJ")
            label2 = line[1]
            line = line[0]
            line = line.split(":")
            label1 = line[1]
            line = line[0].replace("GDY", "")
            if "=" in line:
                whole = line.replace(" ", "").split("=")
                mode = "=="
            else:
                if ">" in line:
                    whole = line.replace(" ", "").split(">")
                else:
                    whole = line.replace(" ", "").split("]")
                mode = ">"
            variable = whole[0]
            operation = whole[1]
            variable = process_math_operation(variable)
            operation = operation.replace("\n", "")
            operation = process_math_operation(operation)
            line = f"{variable}{mode}{operation}"
            if label1 == "NASTEPNY":
                t = "//"
            if label2 == "NASTEPNY":
                t2 = "//"
            label1, label2 = label1[:4], label2[:4]
            output_file.write("    if (" + line + ") {\n")
            output_file.write(f"        {t}goto _{label1};\n")
            output_file.write("    } else {\n")
            output_file.write(f"        {t2}goto _{label2};\n")
            output_file.write("    }\n")
            zline_zindex += 4
            continue

        #################
        # PISZ NA BEBEN #
        #################
        if beben_pisz_c:
            line = line.replace(" ", "").replace("\n", "").replace("PISZNABEBENOD", "").split(":", 1)
            index = process_math_operation(line[0])
            line = line[1].split(",")
            FILE = "FILE *" * ("file" not in used_variables) + ""
            FILE2 = "FILE *" * ("file2" not in used_variables) + ""
            if "file" not in used_variables: used_variables.append("file")
            if "file2" not in used_variables: used_variables.append("file2")
            output_file.write(f"    {FILE} file = fopen(\"drum.txt\", \"r\");\n")
            output_file.write("    if (file == NULL) {\n")
            output_file.write("        file = fopen(\"drum.txt\", \"w\");\n")
            output_file.write("        fclose(file);\n")
            output_file.write("        file = fopen(\"drum.txt\", \"r\");\n")
            output_file.write("    }\n")
            output_file.write(f"    {FILE2} file2 = fopen(\"drum.tmp\", \"w\");\n")
            output_file.write("    if (file != NULL) {\n")
            output_file.write(f"        for (int i = 0; {index} > i; i++) {{\n")
            output_file.write("            fgets(input, sizeof(input), file);\n")
            output_file.write("            if (input[0] == 0) {\n")
            output_file.write("                fprintf(file2, \"\\n\");\n")
            output_file.write("            } else {\n")
            output_file.write("                fprintf(file2, input);\n")
            output_file.write("            }\n")
            output_file.write("        }\n")
            for i in line:
                if i.startswith("*"):
                    is_float = "f" * (i not in integers) + "i" * (i in integers)
                    is_float2 = "float" * (i not in integers) + "int" * (i in integers)
                    is_float3 = "f" * (i not in integers) + "d" * (i in integers)
                    ptr = f"{is_float2}* ptr{is_float}"
                    output_file.write(f"        {ptr} = {i[1:]};\n")
                    output_file.write(f"        for (int i = 0; i < elm({i[1:]}); ++i) {{\n")
                    output_file.write(f"            fprintf(file2, \"%{is_float3}\\n\", *ptr{is_float});\n")
                    output_file.write("            fgets(input, sizeof(input), file);\n")
                    output_file.write(f"            ptr{is_float}++;\n")
                    output_file.write("        }\n")
                    zline_zindex += 6
                else:
                    i = process_math_operation(i)
                    # Added option to write constants, not only variables :)
                    # Just some innovation
                    t = is_number(i)
                    if t == "float":
                        is_float = "f"
                    elif t == "int":
                        is_float = "d"
                    else:
                        t2 = re.sub(r'\[.*?\]', '', i)
                        is_float = "f" * (i not in integers and f"*{t2}" not in integers) + "d" * (i in integers or f"*{t2}" in integers)
                    output_file.write(f"        fprintf(file2, \"%{is_float}\\n\", {i});\n")
                    output_file.write("        fgets(input, sizeof(input), file);\n")
                    zline_zindex += 2
            output_file.write("        while(fgets(input, sizeof(input), file) != NULL) {\n")
            output_file.write("            fprintf(file2, input);\n")
            output_file.write("        }\n")
            output_file.write("        fclose(file);\n")
            output_file.write("        fclose(file2);\n")
            output_file.write("    } else {\n")
            output_file.write("        printf(\"Error: Unable to access drum storage.\\n\");\n")
            output_file.write("    }\n")
            output_file.write("    remove(\"drum.txt\");\n")
            output_file.write("    rename(\"drum.tmp\", \"drum.txt\");\n")
            zline_zindex += 25
            continue

        ##################
        # CZYTAJ Z BEBNA #
        ##################
        if beben_czytaj_c:
            line = line.replace(" ", "").replace("\n", "").replace("CZYTAJZBEBNAOD", "").split(":", 1)
            index = process_math_operation(line[0])
            line = line[1].split(",")
            if line[len(line)-1] == "-":
                moved_List_CZzB = True
                line.pop()
            if len(line) == 0:
                continue
            FILE = "FILE *" * ("file" not in used_variables) + ""
            if "file" not in used_variables: used_variables.append("file")
            output_file.write(f"    {FILE} file = fopen(\"drum.txt\", \"r\");\n")
            output_file.write("    if (file != NULL) {\n")
            output_file.write(f"        for (int i = 0; {index} > i; i++) {{\n")
            output_file.write("            fgets(input, sizeof(input), file);\n")
            output_file.write("        }\n")
            t = line[0].replace("*", "")
            for z, i in enumerate(line):
                vart = re.sub(r'\[.*?\]', '', i)
                if "*" in i:
                    i = i.replace("*", "")
                    i = process_math_operation(i)
                    is_float = "f" * ((i not in integers) and (f"*{vart}" not in integers)) + "i" * ((i in integers) or (f"*{vart}" in integers))
                    is_float2 = "float" * ((i not in integers) and (f"*{vart}" not in integers)) + "int" * ((i in integers) or (f"*{vart}" in integers))
                    ptr = f"{is_float2}* ptr{is_float}" if f"ptr{is_float}" not in used_variables else f"ptr{is_float}"
                    if f"ptr{is_float}" not in used_variables: used_variables.append(f"ptr{is_float}")
                    output_file.write(f"    {ptr} = (void*){i};\n")
                    output_file.write(f"    for (int i = 0; elm({i}) > i; i++) {{\n")
                    output_file.write("        if (fgets(input, sizeof(input), file) == NULL) {\n")
                    output_file.write("            break;\n")
                    output_file.write("        }\n")
                    output_file.write("        char* trimmedInput = input;\n")
                    output_file.write("        while (*trimmedInput == ' ') {\n")
                    output_file.write("            trimmedInput++;\n")
                    output_file.write("        }\n")
                    output_file.write("        if (isdigit(*trimmedInput) || *trimmedInput == '+' || *trimmedInput == '-') {\n")
                    output_file.write("            char* token = strtok(trimmedInput, \" \\n\");\n")
                    output_file.write("            while (token != NULL) {\n")
                    output_file.write(f"                *ptr{is_float} = ato{is_float}(token);\n")
                    output_file.write(f"                ptr{is_float}++;\n")
                    output_file.write("                token = strtok(NULL, \" \\n\");\n")
                    output_file.write("            }\n")
                    output_file.write("        } else {\n")
                    output_file.write("            char* delimiter = strpbrk(trimmedInput, \":=\");\n")
                    output_file.write("            if (delimiter != NULL) {\n")
                    output_file.write("                trimmedInput = delimiter + 1;\n")
                    output_file.write("            }\n")
                    output_file.write("            char* token = strtok(trimmedInput, \" \\n\");\n")
                    output_file.write("            while (token != NULL) {\n")
                    output_file.write(f"                *ptr{is_float} = ato{is_float}(token);\n")
                    output_file.write(f"                ptr{is_float}++;\n")
                    output_file.write("                token = strtok(NULL, \" \\n\");\n")
                    output_file.write("            }\n")
                    output_file.write("        }\n")
                    output_file.write("    }\n")
                    zline_zindex += 32
                else:
                    i = process_math_operation(i)
                    is_float = "float" * ((i not in integers) and (f"*{vart}" not in integers) and (i not in used_variables) and (vart not in used_variables)) + "int" * ((i not in used_variables) and (vart not in used_variables)) * ((i in integers) or (f"*{vart}" in integers))
                    is_float2 = "f" * ((i not in integers) and (f"*{vart}" not in integers)) + "i" * ((i in integers) or (f"*{vart}" in integers))
                    output_file.write(f"    {is_float} {i};\n")
                    output_file.write("    fgets(input, sizeof(input), file);\n")
                    output_file.write(f"    char* spacePtr = strchr(input, ' ');\n")
                    output_file.write("    while (spacePtr) {\n")
                    output_file.write("        memmove(spacePtr, spacePtr + 1, strlen(spacePtr));\n")
                    output_file.write(f"        spacePtr = strchr(input, ' ');\n")
                    output_file.write("    }\n")
                    output_file.write("    if (isdigit(input[0]) || input[0] == '+' || input[0] == '-') {\n")
                    output_file.write(f"        {i} = ato{is_float2}(input);\n")
                    output_file.write("    } else {\n")
                    output_file.write("         char *ptr = strchr(input, ':');\n")
                    output_file.write("         if (!ptr) ptr = strchr(input, '=');\n")
                    output_file.write("         if (ptr) {\n")
                    output_file.write("             memmove(input, ptr + 1, strlen(ptr));\n")
                    output_file.write(f"             {i} = ato{is_float2}(input);\n")
                    output_file.write("         }\n")
                    output_file.write("    }\n")
                    zline_zindex += 17
            output_file.write("    } else {\n")
            output_file.write("        printf(\"Error: Unable to access drum storage.\\n\");\n")
            output_file.write("    }\n")
            output_file.write(f"    fclose(file);\n")
            zline_zindex += 8
            continue

        ########
        # STOP #
        ########
        if stop != -1:
            output_file.write("    return 0;\n")
            continue


        ##########
        # KONIEC #
        ##########
        if koniec != -1:
            line = line.replace("\n", "")
            line = line.replace(" ", "")
            if len(line) > 6:
                if ":" in line:
                    output_file.write("}\n")
            else:
                output_file.write("}\n")
            break

        return 2, error_line_index + 1, last_label

    ##########
    # ERRORS #
    ##########
    if len(loop_labels) != 0:
        return 26, error_line_index, last_label

    return 0, error_line_index, last_label


def main():
    # Define globals
    global loops
    global array_names
    global loop_labels2
    loop_labels2 = []
    loops = 0
    array_names = []
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Compile SAKO to C.")
    parser.add_argument('input_filename', help='Name of the input file')
    parser.add_argument('-en', '--encoding', metavar='{KW6|ASCII|Ferranti}', default='', help='Specify the encoding flag used to process strings.')
    parser.add_argument("-k", "--keys", nargs='+', type=int, help="Numbers of keys set to on. Values from 0 to 35.")
    parser.add_argument('-d', '--debug', action='store_true', help='Turn off removing temporary C file after compilation.')
    parser.add_argument('-Wall', '--all-warnings', action='store_true', help='Turn on -Wall flag while compiling using GCC.')
    parser.add_argument('-nc', '--no-compiling', action='store_true', help='Turn off compiling C code using GCC.')

    # Parse the command-line arguments
    args = parser.parse_args()
    input_filename = args.input_filename
    encoding = args.encoding
    keys_list = args.keys
    debug = args.debug
    wall_b = args.all_warnings
    nc = args.no_compiling

    if not os.path.isfile(input_filename):
        print("Error: Input file does not exist")
        sys.exit(1)

    # Create the output filename without the extension
    output_filename = os.path.splitext(input_filename)[0]

    # Add ".tmp" extension
    tmp_b = ".tmp" * (not nc)
    tmp_output_filename = output_filename + f"{tmp_b}.c"

    # Set keys to on
    keys_on = [0] * 36
    if keys_list != None:
        for i in keys_list:
            keys_on[i] = 1
    keys_on = str(keys_on).replace("[", "{").replace("]", "}")

    try:
        tmp = open(tmp_output_filename, 'w')
        tmp.close()
        with open(input_filename, 'r') as input_file, open(tmp_output_filename, 'r+') as output_file:
            output_file.truncate()
            result, error_index, label = compile(input_file, output_file, encoding, keys_on)
            # print("Now only loops left!!")
        with open(tmp_output_filename, "r+") as file:
            lines = file.readlines()
            # print(loop_labels2)
            for i in reversed(loop_labels2):
                # print(i)
                loops -= 1
                i[2] = f"{i[2]}    LS{loops}:\n"
                lines.insert(i[1]-1, i[2])
            file.seek(0)  # Move the file pointer to the beginning
            file.writelines(lines)

        if not nc and result == 0:
            # Compile the generated C code into an executable
            wall = "-Wall" * wall_b
            compile_command = f"gcc {tmp_output_filename} -lm -fsingle-precision-constant -Os {wall} -o {output_filename}"
            subprocess.run(compile_command, shell=True, check=True)
        elif result != 0:
            print(f"{label} {error_index} BLAD {result} GLOW")

    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)

    if not debug and not nc:
        os.remove(tmp_output_filename)

    return 0;

if __name__ == "__main__":
    main()
