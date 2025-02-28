#!/bin/bash
output="../.github/README.md"

cat <<EOF > "$output"
# Celery Experiments Index

...

## Experiments

EOF

for dir in ../*/; do
    if [ -f "$dir/README.md" ]; then
        # 取得目錄名稱（去除尾端斜線）
        dir_name=$(basename "$dir")

        # 提取目錄名稱前的數字前綴，例如 01、02
        prefix=${dir_name%%_*}
        
        # 提取 <span id="title"> 與 </span> 之間的內容（假設內容在一行）
        title=$(sed -n 's/.*<span id="title">\(.*\)<\/span>.*/\1/p' "$dir/README.md" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
        
        # 提取從 <span id="description"> 到 </span> 之間的多行內容
        desc_raw=$(sed -n '/<span id="description">/,/<\/span>/p' "$dir/README.md")
        description=$(echo "$desc_raw" | sed '1s/.*<span id="description">//; $s/<\/span>.*//' | perl -pe 's/^\s+//s; s/\s+$//s')
        
        # 如果 description 為空，則設為 "- -"
        if [ -z "$description" ]; then
            description="\- -"
        fi

        echo "### [$prefix - $title]($dir/README.md)" >> "$output"
        echo "" >> "$output"
        echo "$description" >> "$output"
        echo "" >> "$output"
    fi
done
