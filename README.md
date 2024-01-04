Simple SAKO Compiler
========

## What is this
This is a very simple and basic SAKO to C compiler. You can consider it as having a basic understanding of SAKO at the A1 proficiency level. It's slow, but it's Python so what would you expect? GCC needed for compilation to a binary file.

## Supported features
- Basic mathematical operations and variable assigning
- Basic array implementation
- Redefining array elements using "=" in index (Multiple value assignment)
- Basic printing and reading to and from stdio
- Labels
- GOTO statements
- If statements
- Loops
- Some of SAKO language functions, mostly skipped functions performing operations on magnetic tapes, disc and directly on RAM

## More notable NOT supported features
- User defined functions
- Changing array's size using `STRUKTURA`
- Operating on array's 0th index by not using "*"
- `ROZDZIAL` declarations
- Using `STOP 𝛼` command to restart program from a label `𝛼`
- Numbers of type "double"
- E notation
- ANY binary and octal operations
- `JEZYK SAS` and `JEZYK SAKO` declarations

## More information
For more information on SAKO programming language I recommend checking out [this repository](https://github.com/Acrimoris/Everything_about_SAKO).
