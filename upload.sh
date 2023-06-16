#!/bin/bash

if [ $# -eq 1 ]; then
    directory="$1"
else
    echo "Usage: $0 <directory>"
    exit
fi

backend=https://35.245.142.242/upload

formData=()
while read -r filename; do
    formData+=(-F "files[]=@$filename; filename=$(echo "$filename" | sed -E 's/^[^/\\]+[/\\][^/\\]+[/\\](.*)/\1/')")
done < <(find ./$directory -type f)

# echo ${formData[@]}
curl -X PUT -H "Content-Type: multipart/form-data" "${formData[@]}" $backend