# coding=utf-8
#utils.py中有些不需要的依赖， 新启一个文件

import sys
import time
import subprocess
import os
def exec_cmd(cmd):
    try:
        if sys.version_info >= (3, 7):
            result = subprocess.run(
                    ["bash", "-c", cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                    encoding='utf-8'
                )
            return result.stdout.strip()
        else:
            result = subprocess.run(
                    ["bash", "-c", cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    check=True,
                    encoding='utf-8'
                )
            return result.stdout.strip()
    except Exception as e:
        pass

def get_last_tag():
    cmd = "git describe --tags --abbrev=0"
    return exec_cmd(cmd)

def get_tag_message(tag):
    cmd = f"git for-each-ref refs/tags/{tag} --format='%(contents:subject)' | sed 's/ *-|* /\\n\\0/g' | sed 's/^ //g' | sed '/^\\s*$/d'"
    return exec_cmd(cmd)

def make_sdk_change_log():
    cmd = "git tag | sort -r -V"
    message = exec_cmd(cmd)

    tags = message.split('\n')
    with open("README.md", 'w', encoding='utf-8') as file:
        title = "# 掘金量化\n\nA股实盘量化 中国期货量化 程序化交易 仿真 中国量化第一 掘金3 sdk\n\n## Changelog\n\n"
        file.write(title)
        for tag in tags:
            if 'rc' in tag:
                continue
            record = f"### Version {tag}\n" + get_tag_message(tag) + "\n\n"
            file.write(record)

        if os.path.exists("README_BAK.md"):
            with open("README_BAK.md", 'r', encoding='utf-8') as bak_file:
                for line in bak_file:
                    file.write(line)
