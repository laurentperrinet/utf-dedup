import unicodedata
import shutil
import filecmp
import os
def path_depth(fname, sep='/'):
   return len(os.path.normpath(fname).split(sep))
def max_depth(fnames, maxdepth = 0):
    for fname in fnames: maxdepth = max(maxdepth, path_depth(fname))
    return maxdepth

from pathlib import Path
norm_form, other_forms = 'NFC', ['NFD', 'NFKD']
def dedup(foldername, pattern='**/*', dry_run=True, verb=False):
    # init glob
    this_path_depth = path_depth(Path(foldername))
    fnames = sorted(Path(foldername).glob(pattern))
    max_path_depth = max_depth(fnames)
    print('Depths to explore = ', max_path_depth, ', Depth of path = ', this_path_depth, ', Files to explore = ', len(fnames))

    # recurse over depths
    for this_depth in range(this_path_depth, max_path_depth+1):
        fnames = sorted(Path(foldername).glob(pattern))
        print('Depth explored = ', this_depth, ' - Files to explore Before filtering', len(fnames))
        fnames_filt = []
        for fname in fnames:
            if path_depth(fname) == this_depth:
                if not str(fname) == str(fname).encode('ascii', 'replace').decode('utf-8') : 
                    fnames_filt.append(fname)
        print('Depth explored = ', this_depth, ' - Files to explore ', len(fnames_filt), '/', len(fnames))
        
        for fname in fnames_filt:
            fname_str = str(fname)
            if not unicodedata.is_normalized(norm_form, fname_str):
                norm_fname = unicodedata.normalize(norm_form, fname_str)
                if dry_run: 
                    print(f'File name {fname_str=} is not in {norm_form=} but so does exist in another form, renaming to {norm_fname=}.')
                else:
                    shutil.move(fname_str, norm_fname)
                if Path(norm_fname) in fnames: fnames.remove(Path(norm_fname))

            for other_form in other_forms:
                other_fname = unicodedata.normalize(other_form, fname_str)
                if not Path(other_fname).exists():
                    if verb: print(f'File name {fname_str=} is in {norm_form=} and does not exist in {other_form=}, all is fine and do nothing.')
                else:
                    if filecmp.cmp(norm_fname, other_fname):
                        if dry_run: 
                            print(f'File name {fname_str=} is in {norm_form=} and does exist in {other_form=}. <<< These are identical - removing other form >>>')
                        else:
                            shutil.move(other_fname, norm_fname)
                            # Path(other_fname).unlink(missing_ok=False)
                        if Path(other_fname) in fnames: fnames.remove(Path(other_fname))                        
                    else:
                        print(f'File {fname_str=} is in {norm_form=} and does exist in {other_form=}. >>> These are different - WARNING !! <<<')
