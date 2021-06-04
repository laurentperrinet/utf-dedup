from pathlib import Path

def is_utf(fname):
   return fname == fname.encode('ascii', 'replace').decode('utf-8')
  
import unicodedata
norm_form, other_form = 'NFC', 'NFD'

import filecmp

def dedup(path, pattern, dry_run=True):

    fnames = sorted(Path(path).glob(pattern))

    for fname in fnames:
        fname_str = str(fname)
        if not is_utf(fname_str):

            is_norm = Path(unicodedata.normalize(norm_form, fname_str)).is_file()
            is_other = Path(unicodedata.normalize(other_form, fname_str)).is_file()
            
            norm_fname = unicodedata.normalize(norm_form, fname_str)
            other_fname = unicodedata.normalize(other_form, fname_str)
   
            if is_norm and not is_other:
                if dry_run: 
                    print(f'File {fname_str=} is in {norm_form=} and does not exist in {other_form=}, do nothing.')
            elif is_norm and is_other:
                if filecmp.cmp(fname_str, other_fname):
                    if dry_run: 
                        print(f'File {fname_str=} is in {norm_form=} and does exist in {other_form=}.')    
                        print('<<< These are identical - removing the other form >>>')
                    else:
                        Path(other_form).unlink()
                    if Path(other_fname) in fnames:
                        fnames.remove(Path(other_fname))

                else:
                    print(f'File {fname_str=} is in {norm_form=} and does exist in {other_form=}.')
                    print('>>> These are different - WARNING !! <<<')
            elif not is_norm and is_other:
                if dry_run: 
                    print(f'File {fname_str=}  does not exist in {norm_form=} but does in {other_form=}, renaming to {norm_fname=}.')
                else:
                     Path(other_fname).rename(norm_fname)
            else:
                print ('This should not happen')
          
