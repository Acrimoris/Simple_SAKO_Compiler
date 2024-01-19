Simple SAKO Compiler
========

## What is this
This is a very simple and basic SAKO to C compiler. You can consider it as having a basic understanding of SAKO at the A1 proficiency level. It's slow, but it's Python, so what would you expect? GCC needed for compilation to a binary file.

## Supported features
- Basic mathematical operations and variable assigning
- Basic array implementation
- Redefining array elements using "=" in index (Multiple value assignment)
- Basic printing and reading to and from stdio
- Labels
- GOTO statements
- If statements
- Loops
- Some of SAKO language functions, mostly skipped functions performing operations on magnetic tapes
- Keys from 0 to 35
- Somewhat intuitive drum storage based on text (With my innovation — writing constants to it)
- Using `STOP 𝛼` command to restart program from a label `𝛼`

## More notable NOT supported features
- User defined functions
- Changing array's size using `STRUKTURA`
- `ROZDZIAL` declarations
- Numbers of type "double"
- ANY binary and octal operations
- `JEZYK SAS` and `JEZYK SAKO` declarations
- Weird loop notation, like `1A)**)*`
- Magnetic tape storage

## Usage
- To use keys in your SAKO program, declare them at the start of the executable using the "-k" command line option. Specify the numbers of keys to turn on, separated by commas. Example: "./program -k 0,5,6,34" This command turns on keys with numbers 0, 5, 6, and 34.
- The drum storage is maintained as plain text, with entries separated by newline characters. Notably, both real and integer numbers occupy the same amount of space, eliminating any distinction in size between the two.

## More information
For more information on SAKO programming language I recommend checking out [this repository](https://github.com/Acrimoris/Everything_about_SAKO).
