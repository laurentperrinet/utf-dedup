import unicodedata
import shutil
import filecmp
# from pathlib import Path
import glob

import os
norm_form, other_forms = 'NFC', ['NFD', 'NFKD']

def path_depth(fname):
   return len(os.path.normpath(fname).split(os.sep))

def max_depth(fnames, maxdepth = 0):
    for fname in fnames: maxdepth = max(maxdepth, path_depth(fname))
    return maxdepth

def glob_utf_fnames(foldername, pattern, this_depth=0):
    fnames = glob.glob(os.path.join(foldername, pattern), recursive=True)
    # print('Depth explored = ', this_depth, ' - Files to explore Before filtering', len(fnames))
    fnames_filt = []
    for fname in fnames:
        if this_depth==0 or path_depth(fname) == this_depth:
            if not str(fname) == str(fname).encode('ascii', 'replace').decode('utf-8') : 
                fnames_filt.append(fname)
    return fnames_filt

def dedup(foldername, pattern='**', dry_run=True, verb=False):
    # init glob
    fnames_filt = glob_utf_fnames(foldername, pattern)
    # computing the range of depths in this list of files
    this_path_depth = path_depth(foldername)
    max_path_depth = max_depth(fnames_filt)
    print('Depths to explore = ', max_path_depth, ', Depth of path = ', this_path_depth, ', Files to explore = ', len(fnames_filt))

    # recurse over depths, from the farther to the closest (with respect to the root folder)
    for this_depth in range(max_path_depth, this_path_depth, -1):
        fnames_filt = glob_utf_fnames(foldername, pattern, this_depth)
        # fnames = sorted(Path(foldername).glob(pattern))
        print('Depth explored = ', this_depth, '/', max_path_depth,  ' - Files to explore ', len(fnames_filt))

        for fname in fnames_filt:
            # https://docs.python.org/3/library/os.path.html#os.path.split
            head, tail = os.path.split(fname)
            norm_fname = os.path.join(head, unicodedata.normalize(norm_form, tail))
            if not fname == norm_fname:
                if dry_run:
                    print(f'File name {fname=} is not in pure {norm_form=}, renaming to {norm_fname=}.')
                if os.path.exists(norm_fname):
                    if filecmp.cmp(norm_fname, other_fname):
                        if os.path.isdir(fname):
                            shutil.move(fname, norm_fname)
                        else:
                            os.rename(fname, norm_fname)
                    else:
                        print(f"file {fname.encode('utf-8')} is in {norm_form=} and does exist in {other_form=} as {other_fname.encode('utf-8')}. >>> these are different - warning !! <<<")

