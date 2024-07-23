/**
 * This is a file containing "deobfuscated" drukuj() function.
 * It's not needed for the compilation.
 * When updating drukuj() function contributor must edit this file together with the oneliner in compiler.py
 **/

#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <math.h>

void drukuj(int I, int J, int is_K, int type, ...){
    I = fabs(I);
    if (I > 50) { I = 50; }
    va_list args;
    va_start(args, type);
    int K = 0;
    int numi = 0;
    float numf = 0;
    K = va_arg(args, int);
    numi = va_arg(args, int);
    numf = (float)va_arg(args, double);
    va_end(args);
    if (is_K == 0) { numi = K; }
    const char* formatTemplate;
    int printedLength = 0;
    int totalWidth = I + J + 1;
    char format[30];
    if (type == 0){
        if (numi >= 0) { formatTemplate = " %%%dd"; }
        else { formatTemplate = "%%%dd"; }
        totalWidth -= 1;
        snprintf(format, sizeof(format), formatTemplate, totalWidth);
    } else if (is_K == 1) {
        int exponent = 0;
        totalWidth += 5;
        if (numf != 0) {
            exponent = (int)floor(log10(fabs(numf)));
            numf /= pow(10, exponent);
        }
        if (numf >= 0) { formatTemplate = "+%%.%dfE%+d "; }
        else { formatTemplate = "%%.%dfE%+d "; }
        double scaling_factor = pow(10, K - 2);
        numf *= scaling_factor;
        snprintf(format, sizeof(format), formatTemplate, J, exponent - K + 2);
    } else {
        if (numf >= 0) { formatTemplate = "%%+%d.%df"; }
        else { formatTemplate = "%%%d.%df"; }
        totalWidth += 1;
        snprintf(format, sizeof(format), formatTemplate, totalWidth, J);
    }
    if (type == 0) {
        printedLength += snprintf(NULL, 0, format, numi);
    } else {
        printedLength += snprintf(NULL, 0, format, numf);
    }
    if (printedLength > totalWidth && type == 1 && is_K == 0) {
        if (numf >= 0) { formatTemplate = "%%+%d.%dE "; }
        else { formatTemplate = "%%%d.%dE "; }
        snprintf(format, sizeof(format), formatTemplate, totalWidth, J);
    }
    if (type == 0) { printf(format, numi); } else { printf(format, numf); }
}

int main() {
    int x = 5;
    float y = 2.5;

    printf("DRUKUJ(3): 5\n");
    drukuj(3, 0, 0, 0, 5);
    printf("\nDRUKUJ(0): 5\n");
    drukuj(0, 0, 0, 0, 5);
    printf("\nDRUKUJ(1): -4\n");
    drukuj(1, 0, 0, 0, -4);
    printf("\nDRUKUJ(1): -1234\n");
    drukuj(1, 0, 0, 0, -1234);
    printf("\nDRUKUJ(3, 2): 24.789\n");
    drukuj(3, 2, 0, 1, 24.789);
    printf("\nDRUKUJ(3, 2): -1.744\n");
    drukuj(3, 2, 0, 1, -1.744);
    printf("\nDRUKUJ(0, 3): 0.02\n");
    drukuj(0, 3, 0, 1, 0.02);
    printf("\nDRUKUJ(1, 2): 23.7\n");
    drukuj(1, 2, 0, 1, 23.7);
    printf("\nDRUKUJ(1, 2): 9.995\n");
    drukuj(1, 2, 0, 1, 9.9999);
    printf("\n\f");
    return 0;
}

