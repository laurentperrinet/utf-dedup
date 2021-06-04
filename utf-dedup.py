import unicodedata
import shutil
import filecmp
import os
def get_depth(path, depth=0):
    if not os.path.isdir(path): return depth
    maxdepth = depth
    for entry in os.listdir(path):
        fullpath = os.path.join(path, entry)
        maxdepth = max(maxdepth, get_depth(fullpath, depth + 1))
    return maxdepth
def get_depth(fname, sep='/'):
   return len(os.path.normpath(fname).split(sep))

from pathlib import Path
norm_form, other_forms = 'NFC', ['NFD', 'NFKD']
def dedup(path, pattern='**/*', dry_run=True, verb=False):
    path_depth = get_depth(path)
    for depth in range(get_depth(path)):
        fnames = sorted(Path(path).glob(pattern))
        # filter non UTF filenames
        for fname in fnames:
            if str(fname) == str(fname).encode('ascii', 'replace').decode('utf-8') or not get_depth(fname) == depth-path_depth: 
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
