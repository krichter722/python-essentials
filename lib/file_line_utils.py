#!/usr/bin/python
# -*- coding: utf-8 -*- 

import re
import os

##############################
# line tools
##############################

# searches for lines which match <tt>old_line_re</tt> and replace every occurance with <tt>new_line</tt> and writes the changes back to the file. If no lines match, nothing happens effectively
def file_replace_line(file_path, old_line_re, new_line):
    if file_path == None:
        raise ValueError("file_path mustn't be None")
    if not os.path.exists(file_path):
        create_file_wrapper(file_path)
    file_obj = open(file_path,"r")
    file_lines = file_obj.readlines()
    file_obj.close()    
    new_file_lines = []
    for file_line in file_lines:
        if re.match(old_line_re, file_line) != None:
            new_file_lines.append(new_line)
        else:
            new_file_lines.append(file_line)
    file_obj = open(file_path, "w")
    file_obj.writelines(new_file_lines)
    file_obj.close()

# retrieves the entry in the <tt>column</tt>th column in the line which has probably been retrieved from a file with lines in form of a table separated by one or more characters matching <tt>whitespace</tt>
def retrieve_column_from_line(line, column, whitespace="\\s"):
    result = re.findall("[^"+whitespace+"]+", line) # findall finds non-overlapping matches
    if len(result) <= column:
        raise ValueError("the requested column doesn't match the number of columns in the specified line")
    return result[column]# creates <code>file_</code> if it doesn't exist

def retrieve_column_values(output, column_count, comment_symbol="#"):
    output_lines0 = filter_output_lines(output, comment_symbol=comment_symbol)
    ret_value = []
    for output_line in output_lines0:
        column_value = retrieve_column_from_line(output_line, column_count)
        ret_value.append(column_value)
    return ret_value

# reads <tt>file_</tt> and returns the return value of <tt>output_lines</tt> invoked with the read file content and the specified <tt>comment_symbol</tt>
# @args comment_symbol can be <code>None</code> in order to include all lines, must not be the empty string '' (<tt>ValueError</tt> will be raised)
def file_lines(file_, comment_symbol="#"):
    if file_ == None:
        raise ValueError("file_ mustn't be None")
    if comment_symbol == "":
        raise ValueError("comment_symbol mustn't be the empty string ''")
    file_obj = open(file_,"r")
    file_content = file_obj.read()
    file_obj.close()
    file_lines = file_content.split("\n")
    ret_value = filter_output_lines(file_lines, comment_symbol)
    return ret_value

# removes all empty lines and lines which start with <tt>comment_symbol</tt> (after eventual whitespace) from <tt>lines</tt> which is supposed to be splitted content of a file or splitted output of a command
# @args comment_symbol can be <code>None</code> in order to include all lines, must not be the empty string '' (<tt>ValueError</tt> will be raised)
def filter_output_lines(lines, comment_symbol="#"):
    if comment_symbol == "":
        raise ValueError("comment_symbol mustn't be the empty string ''")
    ret_value = []
    for i in lines:
        i = i.strip()
        if comment_symbol is None:
            if i != "":
                ret_value.append(i)
        else:
            if not re.match("[\\s]*"+comment_symbol+".*", i) and re.match("[\\s]+", i) == None and i != "":
                if not comment_symbol in i:
                    ret_value.append(i)
                else:
                    ret_value.append(i[:i.find(comment_symbol)])
    return ret_value

# finds all lines in <tt>file_</tt> which match <tt>pattern</tt>.
# @args comment_symbol can be <code>None</code> in order to include all lines, must not be the empty string '' (<tt>ValueError</tt> will be raised)
# @return a list with all line which match <tt>pattern</tt> or an empty list if none matches <tt>pattern</tt>, never <code>None</tt>
# @see file_lines_match for a fail-fast behavior which just indicates whether a matching line has been found using a boolean
def file_lines_matches(file_,pattern,comment_symbol="#"):
    if comment_symbol == "":
        raise ValueError("comment_symbol mustn't be the empty string ''")
    retvalue = []
    filelines = file_lines(file_,comment_symbol) # comment lines are already skipped here
    return output_lines_matches(filelines,pattern,comment_symbol=comment_symbol)

def output_lines_matches(lines, pattern, comment_symbol="#"):
    retvalue = []
    lines = filter_output_lines(lines, comment_symbol=comment_symbol) # remove comment lines and 
    for line in lines:
        if re.match(pattern,line) != None:
            retvalue.append(line)
    return retvalue

# checks whether at least one (non-commented) line matches <tt>pattern</tt> and returns <code>True</code> if this is the case. The method does the same like <tt>file_lines_matches</tt> with fail-fast behavior.
# @args comment_symbol can be <code>None</code> in order to include all lines, must not be the empty string '' (<tt>ValueError</tt> will be raised)
# @return <code>True</code> if at least one line matches <tt>pattern</tt>, <code>False</code> otherwise
def file_lines_match(file_, pattern, comment_symbol="#"):
    if comment_symbol == "":
        raise ValueError("comment_symbol mustn't be the empty string ''")
    file_lines0 = file_lines(file_, comment_symbol=comment_symbol) # comment lines are already skipped here
    return output_lines_match(file_lines0, pattern, comment_symbol=comment_symbol)

# @args comment_symbol can be <code>None</code> in order to include all lines, must not be the empty string '' (<tt>ValueError</tt> will be raised)
def output_lines_match(lines, pattern, comment_symbol="#"):
    if comment_symbol == "":
        raise ValueError("comment_symbol mustn't be the empty string ''")
    lines = filter_output_lines(lines,comment_symbol=comment_symbol)
    for line in lines:
        if re.match(pattern, line):
            return True
    return False

# @args line the line to be commented out (can be a regular expression or a literal) (leading and trailing whitespace in lines in the file will be ignored)
# @args comment_symbol can be <code>None</code> in order to include all lines, must not be the empty string '' (<tt>ValueError</tt> will be raised)
def comment_out(file0, line, comment_symbol):
    if comment_symbol == "":
        raise ValueError("comment_symbol mustn't be the empty string ''")
    new_lines = []
    file_lines0 = file_lines(file0, comment_symbol=None)
    for file_line in file_lines0:
        if not re.match("[\\s]*%s[\\s]*" % line):
            new_lines.append(file_line)
        else:
            new_lines.append("%s %s" % (comment_symbol, line))
    file_obj = open(file0, "rw+")
    for new_line in new_lines:
        file_obj.write("%s\n" % new_line)
    file_obj.close()
    
# @args line the line to be commented in (can be a regular expression or a literal)
def comment_in(file0, line, comment_symbol):
    new_lines = []
    file_lines0 = file_lines(file0, comment_symbol=None)
    for file_line in file_lines0:
        if not re.match("[\\s]*%s[\\s]*%s" % (comment_symbol, line), line):
            new_lines.append(file_line)
        else:
            new_lines.append(re.search(line, file_line).group(0))
    file_obj = open(file0, "rw+")
    for new_line in new_lines:
        file_obj.write("%s\n" % new_line)
    file_obj.close()

def create_file_wrapper(path):
    if not check_os.check_python3():
        file_obj = open(path, "w") # opening for writing or appending creates a non-existant file
        file_obj.close()
    else:
        file_obj = open(path, "x")
        file_obj.close()

