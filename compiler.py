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

def process_math_operation(math_operation: str, user_functions=[]) -> str:
    SAKO_functions = ["SIN", "COS", "TG", "ASN", "ACS", "ATG", "ARC", "PWK", "PWS", "LN", "EXP", "MAX", "MIN", "MOD", "SGN", "ABS", "ENT", "DIV", "SUM", "ILN", "ELM", "ADR", "CCC"]
    C_functions = ["sin", "cos", "tan", "asin", "acos", "atan", "arcus", "sqrt", "cbrt", "log", "exp", "fmax", "fmin", "fmod", "sgn", "fabs", "(int)floor", "div", "sum", "iln", "elm", "*&", "read_int"]
    double_functions = ["DOD", "ODD", "MND", "DZD", "ABD", "IDK", "IKD"]
    read_double = "CZD"
    print_double = "DRD"

    # Check for ()
    if math_operation == "()":
        return ""

    # Replace variables with four characters
    math_operation = re.sub(r'\b([A-Z]+([0-9]*[A-Z]*)*)\b', lambda match: match.group(1)[:4], math_operation)

    # Get rid of preceding zeros to avoid accidental octals
    # Use regex to find numbers and remove leading zeros
    math_operation = re.sub(r'(?<!\.)\b0+(\d+)\b', r'\1', math_operation)

    # Handle square brackets
    math_operation = handle_square_brackets(math_operation)

    # Replace "*" with "$" for further processing
    math_operation = math_operation.replace('*', '$')

    # Handle numbers of type double
    # Probably will need reworking
    # Expecially this huge function
    #
    # Handle doubles being assigned a value
    operations_list = "+-/×⋄$"
    if math_operation[:2] == "($" and math_operation[-1:] == ")" and not any(char in operations_list for char in math_operation[2:][:-1]) and len(math_operation) <=7 and math_operation[2:][:-1] in array_names:
        math_operation = math_operation[2:][:-1]
        math_operation = f"*((double*){math_operation})"
    # Handle doubles in functions
    elif any(sub in math_operation for sub in double_functions):
        math_operation = handle_doubles(math_operation, double_functions)
    # Reading doubles
    elif math_operation.startswith(f"{read_double}("):
        math_operation = math_operation.replace("$", "(double*)&")
    elif math_operation.startswith(read_double):
        print("No support yet for assignments like (*A) = CZD")
    # Printing doubles
    # TODO: Add support for S argument and better K support
    elif math_operation.startswith(f"{print_double}("):
        t = math_operation.split(",")[0].replace("DRD(", "")
        math_operation = math_operation.replace(t, f"*((double *){t[1:]})")
        if math_operation.count(",") >= 3:
            math_operation = math_operation.split(",")
            math_operation.insert(3, "1")
            math_operation = ",".join(math_operation)
        else:
            math_operation = math_operation.split(",")
            math_operation[2] = math_operation[2][:-1]
            math_operation.insert(3, "0)")
            math_operation = ",".join(math_operation)

    # Handle "to the power of" operations
    # Temporarily disabled, waiting for doubles.
    while "$" in math_operation:
        t = math_operation.split("$", 1)
        operations_list="()×⋄-+/[],"
        x = ""
        count = 0
        for i in reversed(t[0]):
            # print("X:", x, i, count)
            if count < 0:
                break
            if i == ")" or i == "]":
                x += i
                count += 1
                continue
            elif i == "(" or i == "[":
                count -= 1
                x += i
                continue
            if i not in operations_list:
                x += i
            else:
                if count != 0:
                    x += i
                else:
                    break
        x = x[::-1]
        y = ""
        count = 0
        for i in t[1]:
            # print("Y:", y, i, count)
            if count < 0:
                y = y[:-1]
                break
            if i not in operations_list:
                y += i
                continue
            else:
                if i == "(" or i == "[":
                    count += 1
                    y += i
                    continue
                elif i == ")" or i == "]":
                    count -= 1
                    y += i
                    continue
            if count != 0:
                y += i
                continue
            else:
                break
        if x[0] == "[" and y[-1] == "]":
            x = x[1:]
            y = y[:-1]
        if x[0] == "(" and y[-1] == ")":
            x = x[1:]
            y = y[:-1]
        math_operation = math_operation.replace(f"{x}${y}", f"pow({x}, {y})")

    # Replace SAKO functions with C functions
    if any(sub in math_operation for sub in SAKO_functions):
        pairs = zip(SAKO_functions, C_functions)
        sorted_pairs = sorted(pairs, key=lambda x: len(x[0]), reverse=True)
        math_operation = reduce(lambda s, pair: s.replace(f"{pair[0]}(", f"{pair[1]}("), sorted_pairs, math_operation)

    # Replace `array_name` with `*array_name` when no index is given
    operations_list="×⋄-+/,])"
    for substring in array_names:
        if math_operation == substring:
            math_operation = f"*{math_operation}"
            break
        index = math_operation.find(substring)
        while index != -1:
            if index + len(substring) < len(math_operation) and math_operation[index + len(substring)] != '[' and math_operation[index + len(substring)] in operations_list and not math_operation[index-1].isalpha() and (math_operation[index - 1] != "(" and math_operation[index - 2] != "m" and math_operation[index - 3] != "l" and math_operation[index - 4] != "e") and (math_operation[index-1] != "&" and (math_operation[index-1] != ")" and math_operation[index-2] != "*" and math_operation[index-3] != "e" and math_operation[index-3] != "l")):
                math_operation = math_operation[:index] + '*' + math_operation[index:]
            index = math_operation.find(substring, index + 2)

    # Replace other operation signs with corresponding C ones
    math_operation = math_operation.replace('×', '*')
    math_operation = math_operation.replace('⋄', '*')

    return math_operation

def handle_square_brackets(math_operation: str) -> str:
    operations_list = "+-/×⋄*"
    new_operation = ""
    part = ""
    count_p = 0
    count_sb = 0
    is_array= False
    for i in math_operation:
        if i in operations_list and count_p + count_sb == 0:
            part += i
            new_operation += part
            part = ""
        elif i == "(":
            is_array = part in array_names or part.split("[")[-1] in array_names or any((part.split(char)[-1] in array_names) for char in operations_list)
            if is_array and part != "":
                part += "["
                count_sb += 1
            else:
                part += i
                count_p += 1
        elif i == ")":
            if part.count("[") - part.count("]") > 0 and count_p == 0:
                part += "]"
                count_sb -= 1
            else:
                part += i
                count_p -= 1
        elif i == "," and count_p == 0:
            part += "]["
        else:
            part += i
    if part != "":
        new_operation += part
    return new_operation

def handle_doubles(math_operation, double_functions):
    def find_matching_paren(s, start):
        stack = []
        for i in range(start, len(s)):
            if s[i] == '(':
                stack.append('(')
            elif s[i] == ')':
                stack.pop()
                if not stack:
                    return i
        return -1

    def process_argument(arg, arg_index, func):
        arg = arg.strip()
        if arg.startswith("$"):
            if arg_index == 2:  # third argument case
                return "(double*)&" + arg[1:]
            else:
                return "*((double*)" + arg[1:] + ")"
        return arg

    def transform_recursive(s):
        i = 0
        while i < len(s):
            for func in double_functions:
                if s[i:].startswith(func):
                    start_idx = s.index('(', i)
                    end_idx = find_matching_paren(s, start_idx)

                    # Process the inner function call recursively first
                    inner_content = s[start_idx+1:end_idx]
                    args = []
                    nested_start = 0
                    j = 0
                    while j < len(inner_content):
                        if inner_content[j] == '(':
                            nested_end = find_matching_paren(inner_content, j)
                            if nested_end != -1:
                                nested_arg = inner_content[nested_start:nested_end+1]
                                nested_transformed = transform_recursive(nested_arg)
                                args.append(nested_transformed)
                                nested_start = nested_end + 1
                                j = nested_end
                        elif inner_content[j] == ',' or j == len(inner_content) - 1:
                            if j == len(inner_content) - 1:
                                j += 1
                            arg = inner_content[nested_start:j].strip()
                            if arg:
                                args.append(arg)
                            nested_start = j + 1
                        j += 1

                    # Transform the arguments
                    new_args = [process_argument(arg, idx, func) for idx, arg in enumerate(args)]
                    new_args_str = ', '.join(new_args)
                    transformed_call = f"{func}({new_args_str})"

                    # Replace the original function call in the math_operation
                    s = s[:i] + transformed_call + s[end_idx+1:]
                    i += len(transformed_call) - 1
                    break
            i += 1
        return s

    return transform_recursive(math_operation)

def compile(input_file, output_file, encoding, eliminate_stop, optional_commands, drum_location):
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
    keys = [0] * 36
    keys = str(keys).replace("[", "{").replace("]", "}")
    restricted_eval = {"__builtins__": None}

    # Add necessary C lines
    output_file.write("#include <stdio.h>\n#include <math.h>\n#include <stdlib.h>\n#include <string.h>\n#include <ctype.h>\n#include <unistd.h>\n#include <errno.h>\n#include <float.h>\n#include <stdarg.h>\n\n")
    output_file.write("#define sum(X, Y, Z) _Generic((Z), int: ({ int sum = 0; for (int X = (Y); X > 0; X--) sum += (Z); sum; }), float: ({ float sum = 0; for (int X = (Y); X > 0; X--) sum += (Z); sum; }))\n")
    output_file.write("#define iln(X, Y, Z) _Generic((Z), int: ({ int iln = 1; for (int X = (Y); X > 0; X--) iln = iln * (Z); iln; }), float: ({ float iln = 1; for (int X = (Y); X > 0; X--) iln = iln * (Z); iln; }))\n")
    output_file.write("#define sgn(X, Y) (((sizeof(X) == sizeof(int)) ? abs(X) : fabsf(X)) * ((Y < 0) ? -1 : 1))\n")
    output_file.write("#define div(num, num2) (_Generic((num) / (num2), int: (int)((num) / (num2)), float: (int)floor((num) / (num2))))\n")
    output_file.write("#define elm(arr) ((int)(sizeof(arr) / sizeof(int)))\n")
    output_file.write("#define arcus(X, Y) (atan2f((Y), (X)) < 0 ? atan2f((Y), (X)) + 2 * M_PI : atan2f((Y), (X)))\n")

    # Add macros and functions for double numbers
    output_file.write("#define GET_MACRO(_1,_2,_3,NAME,...) NAME\n")
    output_file.write("double DOD2(double num, double num2) { return num + num2; }\n")
    output_file.write("void DOD3(double num, double num2, double* num3) { *num3 = num + num2; }\n")
    output_file.write("#define DOD(...) GET_MACRO(__VA_ARGS__, DOD3, DOD2)(__VA_ARGS__)\n")
    output_file.write("double ODD2(double num, double num2){ return num - num2; }\n")
    output_file.write("void ODD3(double num, double num2, double* num3) { *num3 = num - num2; }\n")
    output_file.write("#define ODD(...) GET_MACRO(__VA_ARGS__, ODD3, ODD2)(__VA_ARGS__)\n")
    output_file.write("double MND2(double num, double num2){ return num*num2; }\n")
    output_file.write("void MND3(double num, double num2, double* num3) { *num3 = num * num2; }\n")
    output_file.write("#define MND(...) GET_MACRO(__VA_ARGS__, MND3, MND2)(__VA_ARGS__)\n")
    output_file.write("double DZD2(double num, double num2){ return num/num2; }\n")
    output_file.write("void DZD3(double num, double num2, double* num3) { *num3 = num / num2; }\n")
    output_file.write("#define DZD(...) GET_MACRO(__VA_ARGS__, DZD3, DZD2)(__VA_ARGS__)\n")
    output_file.write("double ABD(double num){ return fabs(num); }\n")
    output_file.write("double IDK(float num){ return (double)num; }\n")
    output_file.write("float IKD(double num){ return (float)num; }\n\n")

    # Specify encoding, used in DRUKUJ/CZYTAJ WIERSZ
    if encoding == "ASCII":
        output_file.write("int encoding[128] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110,111,112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127};\n\n")
    elif encoding == "Ferranti":
        output_file.write("int encoding[128] = {63, -1, 59, -1, -1, -1, -1, -1, -1, -1, 13, -1, -1, 30, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 14, -1, -1, -1, 62, -1, -1, -1, 5, 6, 3, 26, 15, 11, 60, 23, 16, 1, 2, 19, -1, 21, 22, 7, 8, 25, 18, -1, -1, 10, 17, 61, -1, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, -1, -1, 9, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,-1, -1, -1, -1, -1,-1, -1, -1, -1, 20, -1, 24, -1};\n\n")
    else:
        output_file.write("int encoding[128] = {61, -1, -1, -1, -1, -1, -1, -1, -1, -1, 58, -1, 60, 62, 20, 47, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 19, -1, -1, -1, -1, 1, -1, -1, -1, -1, -1, -1, 12, 3, 6, 5, 4, 10, 8, 2, 9, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 11, 7, 16, 13, 17, 18, -1, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 14, -1, 15, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 59, 63};\n\n")

    # Two big functions for reading and printing doubles
    output_file.write("void DRD(double num, int I, int J, int is_K, ...){ va_list args; va_start(args, is_K); int K = 0; float S = 0.0; K = va_arg(args, int); S = (float)va_arg(args, double); va_end(args); int minusI = S-S; int minusJ = 0; const char* formatTemplate; int printedLength = 0; if (I < 0) { minusI = 1; I = fabs(I); } if (J < 0) { minusJ = 1; J = fabs(J); } if (K < 0 && is_K == 1) { minusI = 1; K = fabs(K); } int totalWidth = I + J + 2; char format[30]; if (num >= 0 && minusI == 0 && minusJ != 1) { formatTemplate = \"%%+%d.%df\"; } else if (num >= 0 && minusI == 1) { formatTemplate = \" %%%d.%df\"; totalWidth -= 1; printedLength -= 1; } else { formatTemplate = \"%%%d.%df\"; } if (minusJ == 1) { snprintf(format, sizeof(format), \"%%%s%d.%df\", num < 0 ? \"-\" : \"0\", totalWidth, J); } else { snprintf(format, sizeof(format), formatTemplate, totalWidth, J); } printedLength += snprintf(NULL, 0, format, num); if (printedLength > totalWidth) { snprintf(format, sizeof(format), \"%%%d.%dE\", totalWidth, J); } printf(format, num); }\n")
    output_file.write("int CZD(double* num) { char input[500]; char convert[500]; double tmp = 0.0; int erno = -1; int i = 0; fgets(input, sizeof(input), stdin); char* ptr = input; while (*ptr != '\\0' && *ptr != '\\n') { if (isdigit(*ptr) || *ptr == '.' || *ptr == '+' || *ptr == '-' || *ptr == 'E') { convert[i] = *ptr; i++; erno = *ptr; ptr++; } else { input[0] = -1; break; } } erno = encoding[erno]; if (input[0] == -1) { erno = -erno; } errno = 0; tmp = strtod(convert, &ptr); if (errno == ERANGE && tmp <= DBL_MIN) { erno = -(erno+64); } else if (errno == ERANGE && tmp == HUGE_VAL) { erno = -(erno+128); } *num = tmp; return erno; }\n\n")

    # DRUKUJ C function
    output_file.write("void drukuj(int I, int J, int is_K, int type, ...){ I = fabs(I); if (I > 50) { I = 50; } va_list args; va_start(args, type); int K = 0; int numi = 0; float numf = 0; K = va_arg(args, int); numi = va_arg(args, int); numf = (float)va_arg(args, double); va_end(args); if (is_K == 0) { numi = K; } const char* formatTemplate; int printedLength = 0; int totalWidth = I + J + 1; char format[30]; if (type == 0){ if (numi >= 0) { formatTemplate = \" %%%dd\"; } else { formatTemplate = \"%%%dd\"; } totalWidth -= 1; snprintf(format, sizeof(format), formatTemplate, totalWidth); } else if (is_K == 1) { int exponent = 0; totalWidth += 5; if (numf != 0) { exponent = (int)floor(log10(fabs(numf))); numf /= pow(10, exponent); } if (numf >= 0) { formatTemplate = \"+%%.%dfE%+d \"; } else { formatTemplate = \"%%.%dfE%+d \"; } double scaling_factor = pow(10, K - 2); numf *= scaling_factor; snprintf(format, sizeof(format), formatTemplate, J, exponent - K + 2); } else { if (numf >= 0) { formatTemplate = \"%%+%d.%df\"; } else { formatTemplate = \"%%%d.%df\"; } totalWidth += 1; snprintf(format, sizeof(format), formatTemplate, totalWidth, J); } if (type == 0) { printedLength += snprintf(NULL, 0, format, numi); } else { printedLength += snprintf(NULL, 0, format, numf); } if (printedLength > totalWidth && type == 1 && is_K == 0) { if (numf >= 0) { formatTemplate = \"%%+%d.%dE \"; } else { formatTemplate = \"%%%d.%dE \"; } snprintf(format, sizeof(format), formatTemplate, totalWidth, J); } if (type == 0) { printf(format, numi); } else { printf(format, numf); }}\n\n")

    # Global variables
    output_file.write(f"int keys[] = {keys}; int opt;\n")
    output_file.write("int main(int argc, char *argv[]) {\n")
    # Oneliner for getting keys
    output_file.write("    while ((opt = getopt(argc, argv, \"k:\")) != -1) { if (opt == 'k') { char *token = strtok(optarg, \",\"); while (token != NULL) { int index = atoi(token); if (index >= 0 && index < 35) { keys[index] = 1; } token = strtok(NULL, \",\"); } } }\n")
    # Input variable
    output_file.write("    char input[120];\n")

    # Define regexes patterns
    match_labels = r"^\s*\**[0-9]+[A-Z]*([0-9]*[A-Z]*)*\)"

    # Define boolean variables
    jezyk_SAS = False
    inside_TEKST = False
    tek_wie2 = False
    inside_TABLICA = False

    moved_List_B = False
    moved_List_CZ = False
    moved_List_DR = False
    moved_List_DRW = False
    moved_List_CZW = False
    moved_List_PnB = False
    moved_List_CZzB = False
    moved_List_DRO = False
    moved_List_CZO = False
    moved_List_SW = False
    moved_List_SW_index = -1

    zline_zindex = 44
    error_line_index = 0
    for line in input_file:
        # Add one to index
        zline_zindex += 1
        error_line_index += 1
        # Get rid of popular unnecessary characters
        line = line.replace("\r", "").replace("\t", "")
        # Debug lines
        #if line.replace("\n", "").replace(" ", "") != "": print(line.replace("\n", ""), zline_zindex)
        # print(integers)
        # Make line case insensitive
        if not inside_TEKST and not jezyk_SAS: line = line.upper()
        if not inside_TEKST and not jezyk_SAS and not inside_TABLICA:
            line = line.replace(" ", "").replace("\n", "")
        # Check for SAKO keywords
        # "start" stays, as I started with this keyword
        start = line.find("TEKST")
        calkowite_c = line.find("CALKOWITE:")
        decimal_operation_c = line.find("=")
        octal_operation_c = line.find("[") if line.find("[") != -1 else line.find("≡")
        stop = line.find("STOP")
        koniec = line.find("KONIEC")
        jump_to = line.find("SKOCZDO")
        comment_c = line.startswith("K)") or line.startswith(":")
        spaces = line.find("SPACJA") if line.find("SPACJA") != -1 else line.find("SPACJI")
        newlines = line.find("LINIA") if line.find("LINIA") != -1 else line.find("LINII")
        gdy_c = line.find("GDY")
        gdy_inaczej_c = line.find(",INACZEJ")
        drukuj_c = line.find("DRUKUJ(")
        blok_c = line.find("BLOK(")
        tablica_c = line.find("TABLICA(")
        if not inside_TABLICA: label_c = re.match(match_labels, line) or re.match(r"^\**\)", line)
        czytaj = line.find("CZYTAJ:")
        loop_c = line.find("POWTORZ")
        skocz_wedlug = line.find("SKOCZWEDLUG")
        drukuj_wiersz = line.find("DRUKUJWIERSZ:")
        czytaj_wiersz = line.find("CZYTAJWIERSZ:")
        strona_c = line.find("STRONA")
        beben_pisz_c = line.find("PISZNABEBENOD")
        beben_czytaj_c = line.find("CZYTAJZBEBNAOD")
        drukuj_oktalnie = line.find("DRUKUJOKTALNIE:")
        czytaj_oktalnie = line.find("CZYTAJOKTALNIE:")
        # if decimal_operation_c and not inside_TABLICA and not inside_TEKST and not jezyk_SAS:
        #     t2 = re.sub(match_labels, "", line)
        #     if re.search(r"^\s*\**\)", line): t2 = re.sub(r"^\**\)", "", line)
        #     if t2.startswith("()="): line = line.replace("()=", "")

        ###############
        # Empty Lines #
        ###############
        if line == "" and inside_TEKST == False and not inside_TABLICA:
            zline_zindex -= 1
            error_line_index -= 1
            continue
        if line.find("STRUKTURA") != -1 and inside_TEKST == False and not inside_TABLICA and not comment_c:
            zline_zindex -= 1
            error_line_index -= 1
            continue

        ############
        # COMMENTS #
        ############
        if comment_c and inside_TEKST == False and not inside_TABLICA and not jezyk_SAS:
            zline_zindex -= 1
            continue
        if (line.startswith("USTAWSKALE") or line.startswith("ZWIEKSZSKALE") or line.startswith("SKALA") or line == "KONIECROZDZIALU") and not inside_TABLICA and not inside_TEKST:
            zline_zindex -= 1
            continue
        if ";" in line and not jezyk_SAS:
            return "Semicolon", error_line_index + 1, last_label

        ########################
        # Optional translation #
        ########################
        if (line.startswith("'") or line.startswith("?")) and inside_TEKST == False and not inside_TABLICA:
            if optional_commands:
                line = line.replace("?", "")
            else:
                zline_zindex -= 1
                continue

        ###############
        # Moved lists #
        ###############
        if "-" in integers:
            line = line.split(",")
            integers.remove("-")
            for z, i in enumerate(line):
                if "*" not in i:
                    i = i[:4]
                    if i != "-":
                        output_file.write(f"    int {i};\n")
                        zline_zindex += 1
                        used_variables.append(i)
                else:
                    i = "*" + i.replace("*", "")[:4]
                line[z] = i
            integers.extend(line)
            zline_zindex -= 1
            continue
        elif moved_List_B:
            line = line.split(",")
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
        elif moved_List_DR:
            t = line
            line = line_DR
            t2 = ""
            t3 = []
            count = 0
            for i in t:
                if count < 0:
                    break
                if str(i) == "(":
                    count += 1
                elif str(i) == ")":
                    count -= 1
                t2 += str(i)
                if i == "," and count == 0:
                    t3.append(t2[:-1])
                    t2 = ""
            if t2 != "":
                t3.append(t2)
            for i in t3:
                if i == "-":
                    moved_List_DR = True
                    t = "$"
                    break
                i = process_math_operation(i)
                output_file.write(f"    drukuj({line}, {i});\n")
                zline_zindex += 1
            zline_zindex -= 1
            if t != "$":
                moved_List_DR = False
            continue
        elif moved_List_CZW:
            line = line.split(",")
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
        elif moved_List_DRW:
            line = line.split(",")
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
        elif moved_List_SW != False:
            line = line.split(",")
            if line[-1] == "-":
                moved_List_SW = True
                line.pop()
            else:
                moved_List_SW = False
            for i in line:
                moved_List_SW_index += 1
                output_file.write(f"        case {moved_List_SW_index}:\n")
                if z == "NASTEPNY":
                    output_file.write(f"            break; //goto _NASTEPNY;\n")
                else:
                    output_file.write(f"            goto _{i[:4]};\n")
            if not moved_List_SW:
                output_file.write("    }\n")
                moved_List_SW_index = -1
            zline_zindex += (len(line)*2)
            continue

        ##########
        # LABELS #
        ##########
        if label_c and not inside_TABLICA and not inside_TEKST and not jezyk_SAS:
            t = re.search(match_labels, line) or re.search(r"^\**\)", line)
            t = t.group(0).replace(")", "")
            t2 = t.replace("*", "")
            t2 = t2[:4]
            if t2 != "":
                output_file.write(f"    _{t2}: ;\n")
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
            line = re.sub(match_labels, "", line)
            if re.search(r"^\s*\**\)", line): line = re.sub(r"^\**\)", "", line)
            zline_zindex += 1

        ############################
        # JEZYK SAS and JEZYK SAKO #
        ############################
        if line == "JEZYKSAS" and inside_TEKST == False and not inside_TABLICA:
            jezyk_SAS = True
            output_file.write("    __asm__ volatile (\n")
            continue
        elif line.replace(" ", "").replace("\n", "") == "JEZYKSAKO" and jezyk_SAS:
            jezyk_SAS = False
            output_file.write("    );\n")
            continue
        elif line.replace(" ", "").replace("\n", "") == "JEZYKSAKO" and not jezyk_SAS:
            return 29, error_line_index, last_label
        elif jezyk_SAS:
            output_file.write(f'        {line}')
            continue

        #########
        # TEKST #
        #########
        if start != -1 and line.find("WIERSZY") != 5 and not inside_TABLICA:
            tek_wie = -1
            inside_TEKST = True
            zline_zindex -= 1
            continue
        elif inside_TEKST:
            tek_wie -= 1
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
        elif start != -1 and line.find("WIERSZY") == 5 and not inside_TABLICA:
            tek_wie2 = True
            tek_wie = 0
            line = line[12:].replace(":", "")
            line = line.replace("*", "**").replace("×", "*").replace('⋄', '*')
            if any(char.isalpha() for char in line):
                return 7, error_line_index, last_label
            try:
                tek_wie = int(eval(line, restricted_eval))
            except Error as e:
                return 7, error_line_index, last_label
            inside_TEKST = True
            zline_zindex -= 1
            continue

        #########
        # GOTOS #
        #########
        if jump_to != -1 and not inside_TABLICA:
            line = line.replace("SKOCZDO", "").replace(":", "")[:4]
            if line != "NASTEPNY":
                output_file.write(f"    goto _{line};\n")
            else:
                zline_zindex -= 1
            continue

        ##########################
        # GOTOS ACCORDINGLY TO X #
        ##########################
        if skocz_wedlug != -1 and not inside_TABLICA:
            line = line.replace("SKOCZWEDLUG", "").split(":")
            t = line[1].split(",")
            variable = line[0].replace("(", "").replace(")", "")
            output_file.write("    switch (" + variable + ") {\n")
            if t[-1] == "-":
                moved_List_SW = True
                t.pop()
            for i, z in enumerate(t):
                output_file.write(f"        case {i}:\n")
                if z == "NASTEPNY":
                    output_file.write(f"            break; //goto _NASTEPNY;\n")
                else:
                    output_file.write(f"            goto _{t[i][:4]};\n")
            if moved_List_SW:
                moved_List_SW_index = i
                zline_zindex -= 1
            else:
                output_file.write("    }\n")
            zline_zindex += (len(t)*2) + 1
            continue


        #########
        # LOOPS #
        #########
        if loop_c != -1 and not inside_TABLICA:
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
                output_file.write("    if (fabs(" + str(step) + "/2.0) <= fabs(" + str(variable)  + "-(" + str(end) + "))) {\n")
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
            values = line.split(":")[1].split(",")
            for z, i in enumerate(values):
                if "*" not in i:
                    i = i[:4]
                    if i != "-":
                        output_file.write(f"    int {i};\n")
                        zline_zindex += 1
                        used_variables.append(i)
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
                        output_file.write(f"{indent}for ({used}{i} = 0; {i} < sizeof({vart}{r})/sizeof({vart}{r2}); ++{i}) {{\n")
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
            if len(line) >= 3 and count != True and line.split("=")[0]=="()":
                line = line.split("=")
                operation = process_math_operation(line[1])
                output_file.write(f"    {operation};\n")
                continue
            elif len(line) >= 3 and count != True:
                is_float = ""
                whole = line.split("=")
                variable = whole[0]
                if variable[:2] == "(*" and variable[-1] == ")":
                    variable = f"(*{variable[2:][:-1][:4]})"
                variable = process_math_operation(variable)
                operation = whole[1]
                if operation[:2] == "(*" and operation[-1] == ")":
                    operation = f"(*{operation[2:][:-1][:4]})"
                operation = process_math_operation(operation, user_functions)
                vart = re.sub(r'\[.*?\]', '', variable)[:4]
                if variable[0] != "*":
                    is_float = "float" * ((variable not in integers) and (f"*{vart}" not in integers) and (variable not in used_variables) and (vart not in used_variables)) + "int" * ((variable not in used_variables) and (vart not in used_variables)) * ((variable in integers) or (f"*{vart}" in integers))
                    if variable not in used_variables and vart not in used_variables: used_variables.append(vart)
                output_file.write(f"    {is_float} {variable} = {operation};\n")
                continue

        if octal_operation_c != -1 and gdy_c == -1 and loop_c == -1 and inside_TABLICA == False:
            line = line.split("[")
            variable = line[0]
            operation = line[1]
            operation = operation.replace("+", "|").replace("-", "~").replace("×", "&").replace("⋄", "&")
            # change SAKO octal numbers to C octal numbers
            t = ""
            for i in operation:
                if i == "." or i.isdigit():
                    t += i
                else:
                    if "." in t:
                        t2 = t.replace(".", "")
                        t2 = f"0{t2}"
                        operation = operation.replace(t, t2)
                    t = ""
            if "." in t:
                t2 = t.replace(".", "")
                t2 = f"0{t2}"
                operation = operation.replace(t, t2)

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
            line = line.replace("BLOK(", "").replace(")", "").split(":")
            values = line[1].split(",")
            line = line[0]
            line = line.split(",")
            for i in line:
                i = i.replace("*", "**").replace("×", "*").replace("⋄", "*") + "+1"
                if any(char.isalpha() for char in i):
                    return 27, error_line_index, last_label
                try:
                    i = eval(i, restricted_eval)
                except Error as e:
                    return 27, error_line_index, last_label
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
        # TODO: Add error detection for amount of declared and given elements
        if tablica_c != -1:
            line = line.replace("TABLICA(", "").replace(")", "").split(":")
            TABLICA_numbers = line[0].split(",")
            for i in range(len(TABLICA_numbers)):
                TABLICA_numbers[i] = (TABLICA_numbers[i]+"+1").replace("*", "**").replace("×", "*").replace('⋄', '*')
                if any(char.isalpha() for char in TABLICA_numbers[i]):
                    return 27, error_line_index, last_label
                try:
                    TABLICA_numbers[i] = int(eval(TABLICA_numbers[i], restricted_eval))
                except Error as e:
                    return 27, error_line_index, last_label
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
            line = line.replace(":", "")
            line = line[6:]
            if line != "":
                spaces = True
            if spaces == True:
                t = process_math_operation(line)
                output_file.write("    for (int i = 0; i < " + t +"; ++i) {\n")
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
            line = line.replace(":", "")
            line = line[5:]
            if line != "":
                newlines = True
            if newlines == True:
                t = process_math_operation(line)
                output_file.write("    for (int i = 0; i < " + str(t) +"; ++i) {\n")
                output_file.write("        printf(\"\\n\");\n")
                output_file.write("    }\n")
                zline_zindex += 2
            else:
                output_file.write("    printf(\"\\n\");\n")
            continue

        ##########
        # STRONA #
        ##########
        if strona_c != -1:
            output_file.write("    printf(\"\\f\");\n")
            continue

        ######################
        # PRINTING VARIABLES #
        ######################
        if drukuj_c != -1:
            if line[-1] == "-":
                moved_List_DR = True
            line = line.replace("DRUKUJ(", "").replace("):", ":").split(":")
            t = line[1]
            line = line[0].replace(",", ".")
            t2 = ""
            t3 = []
            count = 0
            for i in t:
                if count < 0:
                    break
                if str(i) == "(":
                    count += 1
                elif str(i) == ")":
                    count -= 1
                t2 += str(i)
                if i == "," and count == 0:
                    t3.append(t2[:-1])
                    t2 = ""
            if t2 != "":
                t3.append(t2)
            #print(t3)
            t = 0
            t2 = ""
            if line.count(".") >= 1:
                line = line.split(".")
                line[0] = process_math_operation(line[0])
                line[1] = process_math_operation(line[1])
                if len(line) == 3:
                    line[2] = process_math_operation(line[2])
                    t2 = f", {line[2]}"
                    t = 1
                line = f"{line[0]}, {line[1]}"
                is_float = "1"
            else:
                line = process_math_operation(line)
                line = f"{line}, 0"
                is_float = "0"
            if t3[-1] == "-":
                moved_List_DR = True
                t3.pop()
            line = f"{line}, {t}, {is_float}{t2}"
            if moved_List_DR:
                line_DR = line
            for i in t3:
                i = process_math_operation(i)
                output_file.write(f"    drukuj({line}, {i});\n")
                zline_zindex += 1
            zline_zindex -= 1
            continue

        ##########
        # CZYTAJ #
        ##########
        if czytaj != -1:
            line = line.replace("CZYTAJ:", "").split(",")
            if line[len(line)-1] == "-":
                moved_List_CZ = True
                line.pop()
            if len(line) == 0:
                zline_zindex -= 1
                continue
            t = line[0].replace("*", "")
            for z, i in enumerate(line):
                vart = re.sub(r'\[.*?\]', '', i)
                if "*" in i:
                    i = "*" + i.replace("*", "")[:4]
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
                    i = process_math_operation(i)
                    vart = re.sub(r'\[.*?\]', '', i)
                    is_float = "float" * ((i not in integers) and (f"*{vart}" not in integers)) + "int" * ((i in integers) or (f"*{vart}" in integers))
                    is_float2 = "f" * ((i not in integers) and (f"*{vart}" not in integers)) + "i" * ((i in integers) or (f"*{vart}" in integers))
                    spacePtr = "char* " if "spacePtr" not in used_variables else ""
                    if "spacePtr" not in used_variables: used_variables.append("spacePtr")
                    if  (i not in used_variables) and (vart not in used_variables):
                        output_file.write(f"    {is_float} {i};\n")
                        used_variables.append(vart)
                        zline_zindex += 1
                    output_file.write("    fgets(input, sizeof(input), stdin);\n")
                    output_file.write(f"    {spacePtr} spacePtr = strchr(input, ' ');\n")
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
                    zline_zindex += 16
            zline_zindex -= 1
            continue

        #################
        # CZYTAJ WIERSZ #
        #################
        if czytaj_wiersz != -1:
            line = line.replace("CZYTAJWIERSZ:", "").split(",")
            for i in line:
                i = i[:4]
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
            line = line.replace("DRUKUJWIERSZ:", "").split(",")
            for i in line:
                i = i[:4]
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

        ###################
        # DRUKUJ OKTALNIE #
        ###################
        if drukuj_oktalnie != -1:
            line = line.replace("DRUKUJOKTALNIE:", "").split(",")
            for i in line:
                i = i[:4]
                if i == "-":
                    moved_List_DRO = True
                    break
                variable = i
                vart = re.sub(r'\[.*?\]', '', variable)[:4]
                is_float = "float" * ((variable not in integers) and (f"*{vart}" not in integers) and (variable not in used_variables) and (vart not in used_variables)) + "int" * ((variable not in used_variables) and (vart not in used_variables)) * ((variable in integers) or (f"*{vart}" in integers))
                if "octal_index" not in used_variables:
                    is_float2 = "int"
                else:
                    is_float2 = ""
                    used_variables.append("octal_index")
                if "octal_parts" not in used_variables:
                    is_float3 = "char"
                else:
                    is_float3 = ""
                    used_variables.append("octal_parts")
                if is_float == "int":
                    output_file.write(f"    {is_float3} octal_parts[4][4];\n")
                    output_file.write(f"    {is_float2} octal_index = 0;\n")
                    output_file.write(f"    while ({i} > 0 || octal_index < 4) {{\n")
                    output_file.write(f"        int part = {i} % 0100;\n")
                    output_file.write(f"        {i} /= 0100;\n")
                    output_file.write("        snprintf(octal_parts[octal_index], sizeof(octal_parts[octal_index]), \"%02o\", part);\n")
                    output_file.write("        octal_index++;\n")
                    output_file.write("    }\n")
                    output_file.write("    for (int i = 3; i >= 0; i--) {\n")
                    output_file.write("        printf(\"%s\", octal_parts[i]);\n")
                    output_file.write("        if (i > 0) {\n")
                    output_file.write("            printf(\".\");\n")
                    output_file.write("        }\n")
                    output_file.write("    }\n")
                    zline_zindex += 14
                else:
                    output_file.write("")
                    zline_zindex += 0
            zline_zindex -= 1
            continue

        ###################
        # CZYTAJ OKTALNIE #
        ###################
        if czytaj_oktalnie != -1:
            line = line.replace("CZYTAJOKTALNIE:", "").split(",")
            for i in line:
                    zline_zindex += 0
            zline_zindex -= 1
            continue

        #######################
        # IF AND KEYS SUPPORT #
        #######################
        if gdy_c != -1 and gdy_inaczej_c != -1:
            if line.startswith("GDYKLUCZ"):
                line = line.split(",INACZEJ")
                t, t2 = "", ""
                label2 = line[1]
                line = line[0]
                line = line.split(":")
                label1 = line[1]
                line = line[0]
                line = line[8:]
                line = process_math_operation(line)
                if label1 == "NASTEPNY":
                    t = "//"
                if label2 == "NASTEPNY":
                    t2 = "//"
                label1, label2 = label1[:4], label2[:4]
                line = f"keys[{line}] == 1"
                output_file.write(f"    if ({line}) {{\n")
                output_file.write(f"        {t}goto _{label1};\n")
                output_file.write("    } else {\n")
                output_file.write(f"        {t2}goto _{label2};\n")
                output_file.write("    }\n")
                zline_zindex += 4
                continue

            if line.startswith("GDYBYLNADMIAR:"):
                line = line.split(",INACZEJ")
                label2 = line[1]
                label2 = label2[:4]
                line = line[0]
                line.replace("GDYBYLNADMIAR:", "")
                label1 = line[:4]
                t = "//" * (label2 == "NAST")
                # There is no detection for that right now, so it's just goto
                output_file.write(f"    {t}goto _{label2};\n")
                continue

            t = t2 = mode = ""
            line = line.split(",INACZEJ")
            label2 = line[1]
            line = line[0]
            line = line.split(":")
            label1 = line[1]
            line = line[0]
            line = line[3:]
            if "=" in line:
                whole = line.split("=")
                mode = "=="
            else:
                if ">" in line:
                    whole = line.split(">")
                else:
                    whole = line.split("]")
                mode = ">"
            variable = whole[0]
            operation = whole[1]
            variable = process_math_operation(variable)
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
        if beben_pisz_c != -1 or moved_List_PnB:
            if not moved_List_PnB:
                line = line[13:].split(":", 1)
                index = process_math_operation(line[0])
                line = line[1].split(",")
            else:
                line = line.split(",")
                zline_zindex -= 19
            if not moved_List_PnB:
                FILE = "FILE *" * ("file" not in used_variables) + ""
                FILE2 = "FILE *" * ("file2" not in used_variables) + ""
                if "file" not in used_variables: used_variables.append("file")
                if "file2" not in used_variables: used_variables.append("file2")
                output_file.write(f"    {FILE} file = fopen(\"{drum_location}\", \"r\");\n")
                output_file.write("    if (file == NULL) {\n")
                output_file.write(f"        file = fopen(\"{drum_location}\", \"w\");\n")
                output_file.write("        fclose(file);\n")
                output_file.write(f"        file = fopen(\"{drum_location}\", \"r\");\n")
                output_file.write("    }\n")
                output_file.write(f"    {FILE2} file2 = fopen(\"{drum_location}.tmp\", \"w\");\n")
                output_file.write("    if (file == NULL) {\n")
                output_file.write("        printf(\"Error: Unable to access drum storage.\\n\");\n")
                output_file.write("        return 1;\n")
                output_file.write("    }\n")
                output_file.write(f"    for (int i = 0; {index} > i; ++i) {{\n")
                output_file.write("        fgets(input, sizeof(input), file);\n")
                output_file.write("        if (input[0] == 0) {\n")
                output_file.write("            fprintf(file2, \"\\n\");\n")
                output_file.write("        } else {\n")
                output_file.write("             fprintf(file2, input);\n")
                output_file.write("        }\n")
                output_file.write("     }\n")

            # Check for moved list
            moved_List_PnB = False
            if line[len(line)-1] == "-":
                moved_List_PnB = True
                line.pop()
            if len(line) == 0:
                zline_zindex -= 1
                continue

            for i in line:
                if i.startswith("*"):
                    is_float = "f" * (i not in integers) + "i" * (i in integers)
                    is_float2 = ("float*" * (i not in integers) + "int*" * (i in integers)) * (i not in used_variables) + ""
                    is_float3 = "f" * (i not in integers) + "d" * (i in integers)
                    if f"ptr{is_float}" not in used_variables: used_variables.append(f"ptr{is_float}")
                    ptr = f"{is_float2} ptr{is_float}"
                    output_file.write(f"    {ptr} = {i[1:]};\n")
                    output_file.write(f"    for (int i = 0; i < elm({i[1:]}); ++i) {{\n")
                    output_file.write(f"        fprintf(file2, \"%{is_float3}\\n\", *ptr{is_float});\n")
                    output_file.write("        fgets(input, sizeof(input), file);\n")
                    output_file.write(f"        ptr{is_float}++;\n")
                    output_file.write("    }\n")
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
            if moved_List_PnB:
                zline_zindex -= 7
            else:
                output_file.write("        while(fgets(input, sizeof(input), file) != NULL) {\n")
                output_file.write("            fprintf(file2, input);\n")
                output_file.write("        }\n")
                output_file.write("    fclose(file);\n")
                output_file.write("    fclose(file2);\n")
                output_file.write(f"    remove(\"{drum_location}\");\n")
                output_file.write(f"    rename(\"{drum_location}.tmp\", \"{drum_location}\");\n")
            zline_zindex += 25
            continue

        ##################
        # CZYTAJ Z BEBNA #
        ##################
        if beben_czytaj_c != -1 or moved_List_CZzB:
            if not moved_List_CZzB:
                line = line[14:].split(":", 1)
                index = process_math_operation(line[0])
                line = line[1].split(",")
            else:
                line = line.split(",")
                zline_zindex -= 8

            if not moved_List_CZzB:
                FILE = "FILE *" * ("file" not in used_variables) + ""
                if "file" not in used_variables: used_variables.append("file")
                output_file.write(f"    {FILE} file = fopen(\"{drum_location}\", \"r\");\n")
                output_file.write("    if (file == NULL) {\n")
                output_file.write("        printf(\"Error: Unable to access drum storage.\\n\");\n")
                output_file.write("        return 1;\n")
                output_file.write("    }\n")
                output_file.write(f"    for (int i = 0; {index} > i; ++i) {{\n")
                output_file.write("        fgets(input, sizeof(input), file);\n")
                output_file.write("    }\n")

            # Check for moved list
            moved_List_CZzB = False
            if line[len(line)-1] == "-":
                moved_List_CZzB = True
                line.pop()
            if len(line) == 0:
                zline_zindex -= 1
                continue

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
                    output_file.write(f"    for (int i = 0; elm({i}) > i; ++i) {{\n")
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
                    vart = re.sub(r'\[.*?\]', '', i)
                    is_float = "float" * ((i not in integers) and (f"*{vart}" not in integers) and (i not in used_variables) and (vart not in used_variables)) + "int" * ((i in integers) or (f"*{vart}" in integers))
                    is_float2 = "f" * ((i not in integers) and (f"*{vart}" not in integers)) + "i" * ((i in integers) or (f"*{vart}" in integers))
                    spacePtr = "char* " if "spacePtr" not in used_variables else ""
                    if "spacePtr" not in used_variables: used_variables.append(f"spacePtr")
                    if  (i not in used_variables) and (vart not in used_variables):
                        output_file.write(f"    {is_float} {i};\n")
                        used_variables.append(vart)
                        zline_zindex += 1
                    output_file.write("    fgets(input, sizeof(input), file);\n")
                    output_file.write(f"    {spacePtr} spacePtr = strchr(input, ' ');\n")
                    output_file.write("    while (spacePtr) {\n")
                    output_file.write("        memmove(spacePtr, spacePtr + 1, strlen(spacePtr));\n")
                    output_file.write(f"        spacePtr = strchr(input, ' ');\n")
                    output_file.write("    }\n")
                    output_file.write("    if (isdigit(input[0]) || input[0] == '+' || input[0] == '-') {\n")
                    output_file.write(f"        {i} = ato{is_float2}(input);\n")
                    output_file.write("    } else {\n")
                    output_file.write("         char *ptr = strchr(input, ':');\n")
                    output_file.write("         if (!ptr) ptr = strchr(input, '=');\n")
                    output_file.write("         memmove(input, ptr + 1, strlen(ptr));\n")
                    output_file.write(f"        {i} = ato{is_float2}(input);\n")
                    output_file.write("    }\n")
                    zline_zindex += 14
            if moved_List_CZzB:
                zline_zindex -= 1
            else:
                output_file.write(f"    fclose(file);\n")
            zline_zindex += 8
            continue

        ########
        # STOP #
        ########
        if stop != -1:
            if eliminate_stop:
                line = line[4:]
                t = "//" * (line == "NASTEPNY") + ""
                line = line[:4]
                output_file.write("    fgets(input, sizeof(input), stdin);\n")
                output_file.write(f"    {t}goto _{line};\n")
            else:
                output_file.write("    return 0;\n")
            continue


        ##########
        # KONIEC #
        ##########
        if koniec != -1:
            output_file.write("}\n")
            break

        return 2, error_line_index + 1, last_label

    ##########
    # ERRORS #
    ##########
    if len(loop_labels) != 0:
        return 26, error_line_index, last_label
    if koniec == -1:
        return 5, error_line_index, last_label

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
    parser.add_argument('-d', '--debug', action='store_true', help='Turn off removing temporary C file after compilation.')
    parser.add_argument('-Wall', '--all-warnings', action='store_true', help='Turn on -Wall flag while compiling using GCC.')
    parser.add_argument('-g', action='store_true', help='Turn on -g flag while compiling using GCC.')
    parser.add_argument('-nc', '--no-compiling', action='store_true', help='Turn off compiling C code using GCC.')
    parser.add_argument('-es', '--eliminate-stop', action='store_true', help='Change STOP command to wait for input and restart from the given label, instead of stopping the programme.')
    parser.add_argument('-ot', '--optional-translation', action='store_true', help='Turn on compiling optional commands.')
    parser.add_argument('-dl', '--drum-location', metavar='{/path/to/file}', default='drum.txt', help='Specify the location of the drum file.')
    parser.add_argument('-o', '--output', metavar='output_file', default='', help='Specify the name of the output file.')

    # Parse the command-line arguments
    args = parser.parse_args()
    input_filename = args.input_filename
    encoding = args.encoding
    debug = args.debug
    wall_b = args.all_warnings
    g_flag = args.g
    nc = args.no_compiling
    eliminate_stop = args.eliminate_stop
    opt_comm = args.optional_translation
    drum_location = args.drum_location
    output_filename = args.output

    if not os.path.isfile(input_filename):
        print(f"{input_filename}: cannot open '{input_filename}': No such file or directory")
        sys.exit(1)

    # Create the output filename without the extension
    if output_filename == "":
        output_filename = os.path.splitext(input_filename)[0]

    # Add ".tmp" extension
    tmp_b = ".tmp" * (not nc)
    tmp_output_filename = output_filename + f"{tmp_b}.c"

    try:
        tmp = open(tmp_output_filename, 'w')
        tmp.close()
        with open(input_filename, 'r') as input_file, open(tmp_output_filename, 'r+') as output_file:
            output_file.truncate()
            result, error_index, label = compile(input_file, output_file, encoding, eliminate_stop, opt_comm, drum_location)
            if result != 0:
                print(f"{label} {error_index} BLAD {result} GLOW")
                return 1;
        with open(tmp_output_filename, "r+") as file:
            lines = file.readlines()
            for i in reversed(loop_labels2):
                loops -= 1
                i[2] = f"{i[2]}    LS{loops}: ;\n"
                lines.insert(i[1]-1, i[2])
            file.seek(0)  # Move the file pointer to the beginning
            file.writelines(lines)

        if not nc and result == 0:
            # Compile the generated C code into an executable
            wall = "-Wall" * wall_b
            g_flag = "-g" * g_flag
            compile_command = f"gcc {tmp_output_filename} -lm -fsingle-precision-constant {g_flag} {wall} -o {output_filename}"
            subprocess.run(compile_command, shell=True, check=True)

    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)

    if not debug and not nc:
        os.remove(tmp_output_filename)

    return 0;

if __name__ == "__main__":
    main()
