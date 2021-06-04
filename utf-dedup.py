import unicodedata
import shutil
import filecmp
import os
def path_depth(fname, sep='/'):
   return len(os.path.normpath(fname).split(sep))
def max_depth(fnames):
    maxdepth = 0
    for fname in fnames:
        maxdepth = max(maxdepth, path_depth(fname))
    return maxdepth

from pathlib import Path
norm_form, other_forms = 'NFC', ['NFD', 'NFKD']
def dedup(path, pattern='**/*', dry_run=True, verb=False):
    fnames = sorted(Path(path).glob(pattern))
    max_path_depth = max_depth(fnames)
    print(max_path_depth, len(fnames))

    for depth in range(max_path_depth):
        fnames = sorted(Path(path).glob(pattern))
        for fname in fnames:
            if str(fname) == str(fname).encode('ascii', 'replace').decode('utf-8') or not (path_depth(fname) - max_path_depth == depth): 
                fnames.remove(fname)
        print(depth, len(fnames))
        for fname in fnames:
            fname_str = str(fname)
            is_name_norm = unicodedata.is_normalized(norm_form, fname_str)
            if not is_name_norm:
                norm_fname = unicodedata.normalize(norm_form, fname_str)
                if dry_run: 
                    print(f'File name {fname_str=} is not in {norm_form=} but does exist in another form, renaming to {norm_fname=}.')
                else:
                    shutil.move(fname_str, norm_fname)
                if Path(norm_fname) in fnames: fnames.remove(Path(norm_fname))

            for other_form in other_forms:
                other_fname = unicodedata.normalize(other_form, fname_str)
                if not Path(other_fname).is_file():
                    if verb: print(f'File name {fname_str=} is in {norm_form=} and does not exist in {other_form=}, all is fine and do nothing.')
                else:
                    if filecmp.cmp(fname_str, other_fname):
                        if dry_run: 
                            print(f'File name {fname_str=} is in {norm_form=} and does exist in {other_form=}. <<< These are identical - removing other form >>>')
                        else:
                            Path(other_fname).unlink(missing_ok=False)
                        if Path(other_fname) in fnames: fnames.remove(Path(other_fname))                        
                    else:
                        print(f'File {fname_str=} is in {norm_form=} and does exist in {other_form=}. >>> These are different - WARNING !! <<<')
