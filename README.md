Simple SAKO Compiler
====================

## What is this
This is a very simple and basic SAKO to C compiler. I have no experience writing transpilers, and didn't do any research, I just went with what seemed the easiest at the moment. You can consider it as having a basic understanding of SAKO at the A1 proficiency level. It's also pretty slow. GCC needed for compilation to a binary file.

## Supported features
- Basic mathematical operations and variable assigning
- Basic array implementation
- Redefining array elements using "=" in index (Multiple value assignment)
- Basic printing and reading to and from stdio
- Labels
- GOTO statements
- If statements
- Loops
- Some of SAKO built-in subroutines, mostly skipped subroutines performing operations on magnetic tapes
- Keys from 0 to 35
- Somewhat intuitive drum storage based on text (With my innovation — writing constants to it)
- Using `STOP 𝛼` command to restart program from a label `𝛼`
- `JEZYK SAS` and `JEZYK SAKO` declarations
- Numbers of type "double"
- Unconvencional loop notation, like `1A)**)*`

## More notable NOT supported features
- User defined subroutines
- Changing array's size using `STRUKTURA`
- `ROZDZIAL` declarations
- ANY binary and octal operations
- Magnetic tape storage
- Extensive subroutines utilisation using `PODSTAW`
- Manipulation and utilisation of chosen devices

## Usage

```
$ python3 compiler.py --help
usage: compiler.py [-h] [-en {KW6|ASCII|Ferranti}] [-d] [-Wall] [-g] [-nc] [-es] [-ot] [-dl {/path/to/file}] [-o output_file] input_filename

Compile SAKO to C.

positional arguments:
  input_filename        Name of the input file

options:
  -h, --help            show this help message and exit
  -en {KW6|ASCII|Ferranti}, --encoding {KW6|ASCII|Ferranti}
                        Specify the encoding flag used to process strings.
  -d, --debug           Turn off removing temporary C file after compilation.
  -Wall, --all-warnings
                        Turn on -Wall flag while compiling using GCC.
  -g                    Turn on -g flag while compiling using GCC.
  -nc, --no-compiling   Turn off compiling C code using GCC.
  -es, --eliminate-stop
                        Change STOP command to wait for input and restart from the given label, instead of stopping the programme.
  -ot, --optional-translation
                        Turn on compiling optional commands.
  -dl {/path/to/file}, --drum-location {/path/to/file}
                        Specify the location of the drum file.
  -o output_file, --output output_file
                        Specify the name of the output file.
```
- To use keys in your SAKO program, declare them at the start of the executable using the "-k" command line option. Specify the numbers of keys to turn on, separated by commas. Example: "./program -k 0,5,6,34" This command turns on keys with numbers 0, 5, 6, and 34.
- The drum storage is maintained as plain text, with entries separated by newline characters. Notably, both real and integer numbers occupy the same amount of space, eliminating any distinction in size between the two.
- `JEZYK SAS` and `JEZYK SAKO` behave like `__asm__ volatile (` and `);` and support C assembly syntax, not SAS syntax.

## More information
For more information on SAKO programming language I recommend checking out [this repository](https://github.com/Acrimoris/Everything_about_SAKO).
