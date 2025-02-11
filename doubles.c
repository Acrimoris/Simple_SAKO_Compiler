/**
 * This is a file containing "deobfuscated" functions for doubles.
 * It's not needed for the compilation.
 * When updating those functions contributor must edit this file together with the oneliner in compiler.py
 **/

/**
 * Reference:
 * System_Automatycznego_KOdowania_SAKO_(Biuro_Projektow_Przemyslu_Syntezy_Chemicznej-Pracownia_Techniki_Obliczeniowej-Gliwice)
 * Page 306 (314)
 **/

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <ctype.h>
#include <errno.h>
#include <float.h>
#include <stdarg.h>

/* First macro */
#define GET_MACRO(_1,_2,_3,NAME,...) NAME

/* I/O */

int encoding[128] = {61, -1, -1, -1, -1, -1, -1, -1, -1, -1, 58, -1, 60, 62, 20, 47, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 19, -1, -1, -1, -1, 1, -1, -1, -1, -1, -1, -1, 12, 3, 6, 5, 4, 10, 8, 2, 9, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 11, 7, 16, 13, 17, 18, -1, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 14, -1, 15, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 59, 63};

// CZD
// Add support for:
// (*A) = CZD
int CZD(double* num) {
    char input[500];
    char convert[500];
    double tmp = 0.0;
    int erno = -1;
    int i = 0;
    fgets(input, sizeof(input), stdin);
    char* ptr = input;
    while (*ptr != '\0' && *ptr != '\n') {
        if (isdigit(*ptr) || *ptr == '.' || *ptr == '+' || *ptr == '-' || *ptr == 'E') {
            convert[i] = *ptr;
            i++;
            erno = *ptr;
            ptr++;
        } else {
            input[0] = -1;
            break;
        }
    }
    erno = encoding[erno];
    if (input[0] == -1) { erno = -erno; }
    errno = 0;
    tmp = strtod(convert, &ptr);
    if (errno == ERANGE && tmp <= DBL_MIN) {
        erno = -(erno+64);
    } else if (errno == ERANGE && tmp == HUGE_VAL) {
        erno = -(erno+128);
    }
    *num = tmp;
    return erno;
}

// DRD
// To finish S, I must first finish octal numbers
// K is almost fully done in drukuj() function
// When I finish it there, I will add it here
void DRD(double num, int I, int J, int8_t is_K, ...){
    va_list args;
    va_start(args, is_K);
    int K = 0;
    float S = 0.0;
    K = va_arg(args, int);
    S = (float)va_arg(args, double);
    va_end(args);
    int minusI = S-S;
    int minusJ = 0;
    const char* formatTemplate;
    int printedLength = 0;
    if (I < 0) {
        minusI = 1;
        I = fabs(I);
    }
    if (J < 0) {
        minusJ = 1;
        J = fabs(J);
    }
    if (K < 0 && is_K == 1) {
        minusI = 1;
        K = fabs(K);
    }
    int totalWidth = I + J + 2;
    char format[30];
    if (num >= 0 && minusI == 0 && minusJ != 1) {
        formatTemplate = "%%+%d.%df";
    } else if (num >= 0 && minusI == 1) {
        formatTemplate = " %%%d.%df";
        totalWidth -= 1;
        printedLength -= 1;
    } else {
        formatTemplate = "%%%d.%df";
    }
    if (minusJ == 1) {
        snprintf(format, sizeof(format), "%%%s%d.%df", num < 0 ? "-" : "0", totalWidth, J);
    } else {
        snprintf(format, sizeof(format), formatTemplate, totalWidth, J);
    }
    printedLength += snprintf(NULL, 0, format, num);
    if (printedLength > totalWidth) {
        snprintf(format, sizeof(format), "%%%d.%dE", totalWidth, J);
    }
    printf(format, num);
}

/* MATH */

// DOD
double DOD2(double num, double num2) { return num + num2; }
void DOD3(double num, double num2, double* num3) { *num3 = num + num2; }
#define DOD(...) GET_MACRO(__VA_ARGS__, DOD3, DOD2)(__VA_ARGS__)

// ODD
double ODD2(double num, double num2){ return num - num2; }
void ODD3(double num, double num2, double* num3) { *num3 = num - num2; }
#define ODD(...) GET_MACRO(__VA_ARGS__, ODD3, ODD2)(__VA_ARGS__)

// MND
double MND2(double num, double num2){ return num*num2; }
void MND3(double num, double num2, double* num3) { *num3 = num * num2; }
#define MND(...) GET_MACRO(__VA_ARGS__, MND3, MND2)(__VA_ARGS__)

// DZD
double DZD2(double num, double num2){ return num/num2; }
void DZD3(double num, double num2, double* num3) { *num3 = num / num2; }
#define DZD(...) GET_MACRO(__VA_ARGS__, DZD3, DZD2)(__VA_ARGS__)

// ABD
double ABD(double num){ return fabs(num); }

/* CONVERSION */

double IKD(float num){ return (double)num; }
float IDK(double num){ return (float)num; }

/* TESTS */

int main() {
    float n[2]={0, 0};
    float n2[2]={0, 0};
    int erno;
    *((double *)n) = IDK(932.363231979643701062);
    *((double *)n2) = IDK(932.863651949643741612);
    erno = CZD((double*)&n);
    printf("1, 2\n");
    DRD(*((double *)n), 1, 2, 0);
    printf("\n3, 2\n");
    DRD(*((double *)n), 3, 2, 1, 3, 3.0);
    printf("\n4, 10\n");
    DRD(*((double *)n), 4, 10, 1, 3, 3.0);
    printf("\n10, 4\n");
    DRD(*((double *)n), 10, 4, 1, 3, 3.0);
    printf("\n-2, 2\n");
    DRD(*((double *)n), -2, 2, 0);
    printf("\n2, -2\n");
    DRD(*((double *)n), 2, -2, 0);
    printf("\n%.30f\n", *((double*)n));
    printf("\n");
    DOD(*((double *)n), *((double *)n2), (double*)&n);
    printf("\n");
    for (double i = 0; i < 2; i+=0.0039629648362916398) {
        *((double *)n)=DOD(*((double *)n), i);
    }
    printf("\n");
    printf("%.30f, %f", n[0], n[1]);
    printf("\n");
    DOD(MND(*((double*)n), *((double*)n)), ODD(*((double*)n), DZD(*((double*)n), *((double*)n2))), (double*)&n2);

    printf("\n");
    DRD(IKD(-1.0), 2, 3, 0);
    printf("\n");
    
    return 0;
}
