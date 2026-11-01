#!/usr/bin/env bash
# Source this file; all changes apply only to the current shell.
passport_idf_root="${AI_PASSPORT_IDF_ROOT:-$HOME/esp/esp-idf-v6.1}"
if [ ! -r "$passport_idf_root/export.sh" ]; then
    echo "ESP-IDF 6.1 not found; set AI_PASSPORT_IDF_ROOT to its checkout." >&2
    return 1
fi
for passport_python_env in "$HOME"/.espressif/python_env/idf6.1_py*_env; do
    if [ -x "$passport_python_env/bin/python" ]; then
        export IDF_PYTHON_ENV_PATH="$passport_python_env"
        export PATH="$passport_python_env/bin:$PATH"
        break
    fi
done
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
. "$passport_idf_root/export.sh" || return 1
unset passport_idf_root passport_python_env
