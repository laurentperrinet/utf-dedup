import unicodedata
import filecmp
from pathlib import Path

def is_utf(fname):
   return not fname == fname.encode('ascii', 'replace').decode('utf-8')
  
norm_form, other_forms = 'NFC', ['NFKC', 'NFD', 'NFKD']

def dedup(path, pattern, dry_run=True, verb=False):

    fnames = sorted(Path(path).glob(pattern))

    for fname in fnames:
        fname_str = str(fname)
        if is_utf(fname_str):
            is_norm = Path(unicodedata.normalize(norm_form, fname_str)).is_file()
            norm_fname = unicodedata.normalize(norm_form, fname_str)
            
            for other_form in other_forms:
                is_other = Path(unicodedata.normalize(other_form, fname_str)).is_file()
                other_fname = unicodedata.normalize(other_form, fname_str)
   
                if is_norm and not is_other:
                    if dry_run: 
                        if verb: print(f'File {fname_str=} is in {norm_form=} and does not exist in {other_form=}, all is fine and do nothing.')
                elif is_other:
                    if is_norm :
                        if filecmp.cmp(fname_str, other_fname):
                            if dry_run: 
                                print(f'File {fname_str=} is in {norm_form=} and does exist in {other_form=}. <<< These are identical - removing other form >>>')
                            else:
                                Path(other_fname).unlink()
                        else:
                            print(f'File {fname_str=} is in {norm_form=} and does exist in {other_form=}. >>> These are different - WARNING !! <<<')
                    else: #if not is_norm and is_other:
                        if dry_run: 
                            print(f'File {fname_str=} does not exist in {norm_form=} but does in {other_form=}, renaming to {norm_fname=}.')
                        else:
                            Path(other_fname).rename(norm_fname)
                    # removing from the list
                    if Path(other_fname) in fnames:
                        fnames.remove(Path(other_fname))
                else:
                    print (f'This should not happen, check {fname_str=}')
