#include <sys/stat.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>

char*
readfile(char* fn)
{
    int fp = open(fn, O_RDONLY);

    struct stat sb;
    stat(fn, &sb);

    char* s = malloc(sb.st_size+1);

    read(fp, s, sb.st_size);
    s[sb.st_size] = '\0';

    close(fp);

    return s;
}
