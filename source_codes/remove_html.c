#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char const *argv[]) {
    int c;
    char tag[16] = {0,};
    char idx     = 0;
    char in_tag  = 0;
    char ignore  = 0;
    while ( ( c = getchar() ) != -1 ) {

        if ( idx < 15 ) {

        }
        if ( ignore ) {
            continue;
        }
        else {
            putchar( c );
        }
    }
    return 0;
}