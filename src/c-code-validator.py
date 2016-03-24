import subprocess
import os
import cStringIO
import re

TMP_FILE_PATH="/tmp/styleGuideDir/"
INDENT_OPTIONS = ['-npro', '-bad', '-bap', '-bbb', '-br', '-blf', '-brs',
                  '-cdw', '-ce', '-fca', '-cli0', '-npcs', '-i4', '-l79',
                  '-lc79', '-nbfda', '-nut', '-saf', '-sai', '-saw', '-sbi4',
                  '-sc', '-sob', '-st', '-ncdb', '-pi4', '-cs', '-bs', '-di1',
                  '-lp', '-il0', '-hnl']

def run_bash_command(cmd, *args):
    exec_cmd = []
    exec_cmd.append(cmd)
    if(len(args)):
        exec_cmd = exec_cmd + list(args)
    exec_cmd = filter(None, exec_cmd)
    print exec_cmd
    try:
        out = subprocess.Popen(exec_cmd, stdout = subprocess.PIPE, stderr = 
                               subprocess.PIPE)
    except Exception as e:
        print "Failed to run the bash command, %s" % e
    res, err_res = out.communicate()
    res = res.strip()
    res = res.strip('\n')
    err = out.returncode
    print res
    if(err):
        print("Failed to run the bash command %d\n%s" %(err, err_res))
    return err, res, err_res

def run_bash_command_with_list_args(cmd, args):
    return(run_bash_command(cmd, *args))

def is_commit_id_valid(commit_id):
    """
    Check if the commit_id present and valid in Git repo
    :param commit_id: The commit id in the git repo
    """
    commit_id = str(commit_id)
    if(commit_id == ''):
        return False
    (exit_code, result, err_res) = run_bash_command("git", "cat-file", "-t",
                                                    commit_id)
    if(exit_code):
        return False
    if(str(result) != "commit"):
        print result
        print str(result)
        return False
    return True

def are_commits_valid(pre_commit_id, post_commit_id):
    if(pre_commit_id and not is_commit_id_valid(pre_commit_id)):
        print("Invalid Pre commit ID")
        return False
    if(post_commit_id and not is_commit_id_valid(post_commit_id)):
        print("Invalid Post commit ID")
        return False
    if(not pre_commit_id):
        pre_commit_id = "HEAD"
        post_commit_id = ""
    return True

def get_file_list(pre_commit_id = "", post_commit_id = ""):
    """
    Function to get list of files thats been changed
    :param pre_commit_id: The git SHA ID where the diff starts(optional).
    :param post_commit_id: The git SHA ID where the diff ends(optional). 
    Uncommitted changes will consider if pre_commit_id is not present.
    Changes including uncommitted will consider if post_commit_id is not given.
    """
    file_list = []
    if(not are_commits_valid(pre_commit_id, post_commit_id)):
        return file_list
    (exit_code, result, err_res) = run_bash_command("git", "diff",
                                                    pre_commit_id,
                                                    post_commit_id, "--stat")
    if(exit_code):
        print("Failed to get the list of files changed")
        return file_list
    file_list = result.split('\n')
    for i in range(len(file_list)):
        file_list[i] = file_list[i].split('|')[0].strip()
    del file_list[-1] #Delete the file stat entry at the last of output.
    return file_list

def get_diff_line_nos(file_a, file_b):
    """
    Grep the line number information from the unified diff between given files
    :param file_a: Source file that get modified to.
    :param file_b: Modified target file
    """
    diff_line_no_set = []
    valid_set = set('0123456789+-,')
    if(not os.path.isfile(file_a) or not os.path.isfile(file_b)):
        print("%s, %s files are not exists in the file system" 
              % (file_a, file_b))
        return diff_line_no_set
    (exit_code, result, err_res) = run_bash_command("diff", "-U0", file_a,
                                                    file_b)
    if(not result):
        print("No diff present between files" % (file_a, file_b))
        return diff_line_no_set
    for line in cStringIO.StringIO(result).readlines():
        if "@@" in line: # Read only the line-numbers that are changes.
            line = line.replace(" ", "").split("@@")[1]
            if(any((char not in valid_set) for char in line)):
                print("Cannot extract the line number information, Wrong line "
                      "%s" % line)
                return diff_line_no_set
            line = re.search(r'\+.*$', line, re.MULTILINE|re.IGNORECASE).group()
            if not line:
                print("Failed to extract changed line numbers, Wrong reg exp")
                return diff_line_no_set
            lineno_list = line.lstrip('+').split(',')
            if(len(lineno_list) == 1):
                lineno_list.append(1)
            diff_line_no_set.append(lineno_list)
    if(not diff_line_no_set):
        print("No lines are changed in the given file %s" % fileName)
        return diff_line_no_set
    print diff_line_no_set

def apply_gnu_indent(fileName):
    if(not os.path.isfile(fileName)):
        print("%s file not exists in the file system" % fileName)
        return 
    arg_list = INDENT_OPTIONS + [fileName]
    (exit_code, result, err_res) = run_bash_command_with_list_args("indent",
                                                                   arg_list)
    target_fd = open(TMP_FILE_PATH + os.path.basename(fileName), 'w')
    target_fd.write(result)

def apply_gnu_indent_for_diffs(input_file, indent_file, diff_line_set):
    """
    Function to apply indent changes only on diffs than entire file.
    :param input_file: The file with diff and not indent applied.
    :param indent_file: The file with diff after indent applied.
    :param diff_line_set: The lines that have been modified.
    """
    
def highlight_code_changes(fileName, pre_commit_id, post_commit_id):
    """
    Mark the code changes to make it ready for verifying the codestyle rules.
    Mark every line of untouched code are commented out with this function.
    :param fileName: The file that modified for hightlight changes.
    :param pre_commit_id: The Commit ID the changes starts
    :param post_commit_id: The commit ID the changes ends.
    """
    diff_line_no_set = []
    valid_set = set('0123456789+-,')
    if(not are_commits_valid(pre_commit_id, post_commit_id)):
        return
    if(not os.path.isfile(fileName)):
        print("%s file not exists in the file system" % fileName)
        return
    (exit_code, result, err_res) = run_bash_command("git", "diff", "-U0",
                                                    pre_commit_id,
                                                    post_commit_id, fileName)
    if(exit_code):
        print("Failed to collect the diff on %s" %fileName)
        return
    if(not result):
        print("No diff present on file %s" % fileName)
    for line in cStringIO.StringIO(result).readlines():
        if "@@" in line: # Read only the line-numbers that are changes in file.
            line = line.replace(" ", "").split("@@")[1]
            if(any((char not in valid_set) for char in line)):
                print("Cannot extract the line number information, Wrong line "
                      "%s" % line)
                return
            line = re.search(r'\+.*$', line, re.MULTILINE|re.IGNORECASE).group()
            if not line:
                print("Failed to extract changed line numbers, Wrong reg exp")
                return
            lineno_list = line.lstrip('+').split(',')
            if(len(lineno_list) == 1):
                lineno_list.append(0)
            diff_line_no_set.append(lineno_list)
    if(not diff_line_no_set):
        print("No lines are changed in the given file %s" % fileName)
        return
    print diff_line_no_set
    file_buf = open(fileName, 'r')
    target_buf = open(TMP_FILE_PATH + os.path.basename(fileName), 'w')
    line_num = 1
    i = 0;
    start_line = int(diff_line_no_set[i][0])
    num_lines = 0
    for line in file_buf.readlines():
        if(line_num == start_line):
            num_lines = int(diff_line_no_set[i][1])
            i = i + 1
            if(i<len(diff_line_no_set)):
                start_line = int(diff_line_no_set[i][0])
        elif(num_lines > 0):
            num_lines = num_lines - 1
        elif(line):
            line = "/*** " + line.rstrip('\n') + " ***/\n"
        target_buf.write(line)
        line_num = line_num + 1
    file_buf.close()
    target_buf.close()


#get_file_list()
#get_file_list(pre_commit_id="a36bb33445acdbc5bfc30ecab8408dac9a99913e")
#get_file_list(post_commit_id="13adc909c3f153995b7f63017959a7dec4833051")
#get_file_list("a36bb33445acdbc5bfc30ecab8408dac9a99913e", "13adc909c3f153995b7f63017959a7dec4833051")
run_bash_command("mkdir", "-p", TMP_FILE_PATH)
#highlight_code_changes("lib/netdev-dpdk.c", "caff23ca82eccaaf4fe3c024566e4b09fa855b0d", "13adc909c3f153995b7f63017959a7dec4833051")
#apply_gnu_indent("lib/netdev-dpdk.c")
get_diff_line_nos("lib/netdev-dpdk.c", "/tmp/styleGuideDir/netdev-dpdk.c")