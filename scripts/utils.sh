#!/bin/sh

transfer() {
    for f in $2; do
        name=$(basename "$f")
        if [ "$name" != "." ] && [ "$name" != ".." ] && [ "$name" != ".linuxbrew" ]; then
            $1 "$f" $3;
        fi
    done
}
