#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>


/**
 * Count the number of tiles in the given root directory.
 *
 * Expects directory to be structured as `/{z}/{x}/{y}/`. If it is not, the
 * count will not be correct!
 */
int
count_tiles_r(char* path, int depth)
{
    DIR* d = opendir(path);
    if (d == NULL) {
        printf("Failed to open %s\n", path);
        return 0;
    }

    int ctr = 0;
    struct dirent* de;
    while ((de = readdir(d)) != NULL)
    {
        if (de->d_name[0] == '.') {
            continue;
        } else if (depth >= 2) {
            ctr++;
        } else {
            char new_path[128];
            sprintf(new_path, "%s/%s", path, de->d_name);
            ctr += count_tiles_r(new_path, depth + 1);
        }
    }

    closedir(d);

    return ctr;
}

int
count_tiles(char *path)
{
    return count_tiles_r(path, 0);
}
