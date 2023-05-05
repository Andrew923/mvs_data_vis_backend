#!/bin/bash

backend=http://localhost:9233

formData=()
while read -r filename; do
    formData+=(-F "files[]=@$filename; filename=$(echo "$filename" | sed -E 's/^[^/\\]+[/\\][^/\\]+[/\\](.*)/\1/')")
done < <(find ./images -type f)

curl -X PUT -H "Content-Type: multipart/form-data" "${formData[@]}" $backend