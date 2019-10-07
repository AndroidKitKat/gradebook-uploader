#!/usr/bin/env python3
''' Script to take LD Gradebooks and format them for Sakai
    (c) 2019 mike 'androidkitkat' eisemann
'''

import csv
import sys # fuck argparse
import os

OUTFILE = 'output.csv'
INFILE = None
OUTFILE_WO_EXTENSION = None
NAMES = []

def usage(status=0):
    '''Display usage information and exit with specified status '''
    print('''Usage: {} [options] gradebook
    -o file     Output file name (default: output.csv)
    '''.format(os.path.basename(sys.argv[0]))
    )
    sys.exit(status)
def import_file(file_name):
    '''
    takes a file and loads it into a structure we can use

    import file structure found in demo/import_temp.csv

    student dict structure: {
        netid1: [name1, q1_comment, q1_deduct, q2_comment, q2_deduct, ..., qN_comment, qN_deduct]
        netid2: [name2, q1_comment, q1_deduct, q2_comment, q2_deduct, ..., qN_comment, qN_deduct]
        netid3: [name3, q1_comment, q1_deduct, q2_comment, q2_deduct, ..., qN_comment, qN_deduct]
        ...
        netidN: [nameN, q1_comment, q1_deduct, q2_comment, q2_deduct, ..., qN_comment, qN_deduct]
    }

    '''
    students = {}
    with open(file_name, 'r') as imp:
        csv_r = csv.reader(imp, delimiter=',')
        col_title = True
        for row in csv_r:
            # skip the titles
            if col_title:
                # num_q = ((len(row) - 1) // 2)
                col_title = False
            else:
                netid = row.pop(0)
                students[netid] = row

    return students

def mod_data(l_s):
    '''
    Alters the data from import to conform to desired output

    If a deduct is empty, turn field into 0
    also builds a master list of names
    '''
    for _k, _v in l_s.items():
        #skims the names off the top
        NAMES.append(_v.pop(0))
        counter = 0
        for i, item in enumerate(_v):
            # change score to 0 if empty
            if counter % 2 != 0 and not item:
                _v[i] = '0'
            elif not item: # i don't know what this does
                _v[i] = 'No comment provided'
            counter += 1
    return l_s

def calc_score(comments):
    '''
    calculates score from comments field
    '''
    score = 100
    for item in comments:
        # tries to total the score
        try:
            score -= abs(int(item))
        except ValueError:
            pass
    return score

def build_comment(netid, comments):
    '''
    input:
        netid:      netid
        comments:   [q1_comment, q1_deduct, q2_comment, q2_deduct, ..., qN_comment, qN_deduct]


    comment format
    -------------
    netid: $netid

    Score: $score

    Comments:
        Problem 1: $deduction; $comment
        Problem 2: $deduction; $comment
        ...
        Problem N: $deduction; $comment
        (if applicable)
    '''
    # num_q = len(comments) // 2
    score = calc_score(comments)

    # build comment
    sakai_comment = '''netid: {}
Score: {}

'''.format(netid, score)

    prblm_num = 1
    # don't put comment header unless they get something wrong
    header = False
    while comments:
        q_com = comments.pop(0)
        q_ded = comments.pop(0)
        if int(q_ded) != 0:
            q_ded = -1 * abs(int(q_ded))
            if not header:
                sakai_comment += 'Comments: \n'
                header = True
            sakai_comment += '''    Problem {}: {:>3}; {}\n'''.format(prblm_num, q_ded, q_com)
        prblm_num += 1

    return sakai_comment, score

def generate_passthru(l_s):
    '''
    since I am bad and don't want to re-make my export_file
    this function takes the input file and generates the template for final export
    '''
    with open('passthru.csv','w') as _pt:
        csv_pt = csv.writer(_pt)
        header_row = ['Student ID', 'Student Name', OUTFILE_WO_EXTENSION + ' [100]', '* ' + OUTFILE_WO_EXTENSION]
        csv_pt.writerow(header_row)
        for netid, junk in l_s.items():
            csv_pt.writerow([netid, NAMES.pop(0)])




def prepare_and_send_data(l_s):
    '''gets the sakai comment and score ready for injection'''
    comments, scores = [], []
    for _k, _v in l_s.items():
        sakai_comment, score = build_comment(_k, _v)
        comments.append(sakai_comment)
        scores.append(score)

    generate_passthru(l_s)
    export_file('passthru.csv', OUTFILE, comments, scores)

def export_file(file_in, file_out, s_c, _s):
    '''
    exports the data loaded in to the supplied file
    '''
 
    with open(file_in, 'r') as _fi, open(file_out, 'w') as _fo:
        csv_fi = csv.reader(_fi, delimiter=',')
        csv_fo = csv.writer(_fo, dialect='excel')
        header = True
        for row in csv_fi:
            # eliminate empty fields
            row = list(filter(None, row))
            if header:
                header = False
            else:
                comment = s_c.pop(0)
                score = _s.pop(0)
                row.append('{}'.format(score))
                row.append('{}'.format(comment))
            csv_fo.writerow(row)




if __name__ == '__main__':
    # parse command line input
    args = sys.argv[1:]
    while len(args) and args[0].startswith('-') and len(args[0]) > 1:
        arg = args.pop(0)
        if arg == '-o':
            OUTFILE = args[0]
            args.pop(0)
        elif arg == '-h':
            usage(0)
        else:
            usage(1)
    # get input file name
    if len(args) > 0:
        INFILE = args[0]

    if not INFILE:
        usage(-1)

    # get outfile without extension
    OUTFILE_WO_EXTENSION = os.path.splitext(OUTFILE)[0]  
    LOADED_STUDENTS = import_file(INFILE)
    LOADED_STUDENTS = mod_data(LOADED_STUDENTS)
    # ugly, but prepare data also sends the data lol
    prepare_and_send_data(LOADED_STUDENTS)
