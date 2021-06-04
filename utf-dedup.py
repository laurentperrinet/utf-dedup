import unicodedata
import filecmp
from pathlib import Path
norm_form, other_forms = 'NFC', ['NFD', 'NFKD']
def dedup(path, pattern, dry_run=True, verb=False):
    fnames = sorted(Path(path).glob(pattern))
    # filter non UTF filenames
    for fname in fnames:
        if str(fname) == str(fname).encode('ascii', 'replace').decode('utf-8'): 
            fnames.remove(fname)
    for fname in fnames:
        fname_str = str(fname)
        is_name_norm = unicodedata.is_normalized(norm_form, fname_str)            
        for other_form in other_forms:
            other_fname = unicodedata.normalize(other_form, fname_str)
            path_other =  Path(other_fname)
            is_other =  path_other.is_file()
            if is_name_norm and not is_other:
                if verb: print(f'File name {fname_str=} is in {norm_form=} and does not exist in {other_form=}, all is fine and do nothing.')
            elif is_name_norm and is_other:
                if filecmp.cmp(fname_str, other_fname):
                    if dry_run: 
                        print(f'File name {fname_str=} is in {norm_form=} and does exist in {other_form=}. <<< These are identical - removing other form >>>')
                    else:
                        Path(other_fname).unlink(missing_ok=False)
                    if Path(other_fname) in fnames: fnames.remove(Path(other_fname))                        
                else:
                    print(f'File {fname_str=} is in {norm_form=} and does exist in {other_form=}. >>> These are different - WARNING !! <<<')
                break
            elif not is_name_norm and is_other:
                norm_fname = unicodedata.normalize(norm_form, fname_str)
                if dry_run: 
                    print(f'File name {fname_str=} is not in {norm_form=} but does exist in {other_form=}, renaming to {norm_fname=}.')
                else:
                    print(other_form, Path(other_fname).is_file(), Path(norm_fname).is_file())
                    Path(other_fname).rename(norm_fname)
                if Path(other_fname) in fnames: fnames.remove(Path(other_fname))                        
                if Path(norm_fname) in fnames: fnames.remove(Path(norm_fname))
                break
