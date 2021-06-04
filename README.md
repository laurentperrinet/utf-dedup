# utf-dedup, a simple utility to remove duplicate filenames


## the story

Syncing files, especially across different OSes can generate duplicate files. For instance, this may happen when copying files from the `src` folder of a remote host `HOST`to a `dst` folder on the local machine:

```
rsync -av HOST:src/ dst
```

You can prevent this by adding a proper option such as

```
rsync -av--iconv=UTF-8-MAC,UTF-8 HOST:src/ dst
```

yet, if it happens, you end up with files which are named similarly, yet the files are duplicated. For instance

```python
%ls Qui*
'Qui êtes-vous, Polly Maggoo.DVDRip.Xvid-KG.avi'  'Qui êtes-vous, Polly Maggoo.DVDRip.Xvid-KG.avi'
```

What happened? Filenames are encoded in [unicode](https://fr.wikipedia.org/wiki/Unicode), but with two different variants for some characters. To simplify, in the example, one encoding uses `ê` while the other represents `ê` as `^` and `e` superposed.

## usage
```python
from utf-dedup import 
path, pattern = '.', 'Qui*'

path, pattern = '.', '**/*'

dedup(path, pattern)

# dedup(path, pattern, dry_run=False) # BE CAREFUL WITH THAT ONE !!
```

## development

Here are the step used during development:

### diagnostic

The python standard library has many useful tools, and [unicodedata](https://docs.python.org/3/library/unicodedata.html) will be perfect to understand what happened inside these filenames and how to mitigate this.

```python
In [4]: fname = 'Qui êtes-vous, Polly Maggoo.DVDRip.Xvid-KG.avi'

In [5]: fname2 = 'Qui êtes-vous, Polly Maggoo.DVDRip.Xvid-KG.avi'
   ...: 

In [6]: fname
Out[6]: 'Qui êtes-vous, Polly Maggoo.DVDRip.Xvid-KG.avi'

In [7]: fname.encode?
Signature: fname.encode(encoding='utf-8', errors='strict')
Docstring:
Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.
Type:      builtin_function_or_method

In [8]: fname.encode('utf-8')
Out[8]: b'Qui e\xcc\x82tes-vous, Polly Maggoo.DVDRip.Xvid-KG.avi'

In [9]: fname2.encode('utf-8')
Out[9]: b'Qui \xc3\xaates-vous, Polly Maggoo.DVDRip.Xvid-KG.avi'

In [10]: repr(fname)
Out[10]: "'Qui êtes-vous, Polly Maggoo.DVDRip.Xvid-KG.avi'"

In [11]: import unicodedata

In [12]: unicodedata.normalize('NFD', fname)
Out[12]: 'Qui êtes-vous, Polly Maggoo.DVDRip.Xvid-KG.avi'

In [13]: unicodedata.normalize('NFD', fname2)
Out[13]: 'Qui êtes-vous, Polly Maggoo.DVDRip.Xvid-KG.avi'

In [14]: unicodedata.normalize('NFD', fname) == unicodedata.normalize('NFD', fname2)
    ...: 
Out[14]: True

In [15]: unicodedata.normalize?
Signature: unicodedata.normalize(form, unistr, /)
Docstring:
Return the normal form 'form' for the Unicode string unistr.

Valid values for form are 'NFC', 'NFKC', 'NFD', and 'NFKD'.
Type:      builtin_function_or_method

In [16]: unicodedata.normalize('NFC', fname) == unicodedata.normalize('NFC', fname2)
Out[16]: True

In [17]: unicodedata.normalize('NFC', fname)
Out[17]: 'Qui êtes-vous, Polly Maggoo.DVDRip.Xvid-KG.avi'

In [18]: unicodedata.normalize('NFC', fname).encode('utf-8')
    ...: 
Out[18]: b'Qui \xc3\xaates-vous, Polly Maggoo.DVDRip.Xvid-KG.avi'

In [19]: unicodedata.normalize('NFD', fname).encode('utf-8')
    ...: 
Out[19]: b'Qui e\xcc\x82tes-vous, Polly Maggoo.DVDRip.Xvid-KG.avi'

In [20]: unicodedata.is_normalized('NFD', fname)
Out[20]: True

In [21]: unicodedata.is_normalized('NFD', fname2)
Out[21]: False

In [22]: unicodedata.is_normalized('NFC', fname2)
Out[22]: True

```

### NFC or NFD ?

Opinions [vary](https://www.win.tue.nl/~aeb/linux/uc/nfc_vs_nfd.html), but ultimately they are compatible and interchangeable. So I chose NFC.


### solving the problem step-by-step

* Let's [glob](https://docs.python.org/3.9/library/pathlib.html#pathlib.Path.glob) some files:

```python

from pathlib import Path
path, pattern = '..', '**/Qui*'

path, pattern = '.', 'Qui*'
fnames = sorted(Path(path).glob(pattern))
```

The “**” pattern means “this directory and all subdirectories, recursively”. In other words, it enables recursive globbing.

* we will cycle over all globed file and do the following:
 * is the file  name coded in utf?

```python
def is_utf(fname):
   return not fname == fname.encode('ascii', 'replace').decode("utf-8")
is_utf(str(fname))
```
  * get the form:

```python
import unicodedata
forms = ['NFC', 'NFKC', 'NFD', 'NFKD']
def get_form(fname):
   for form in forms:
       if unicodedata.is_normalized(form, fname): break
   return form

In [35]: [get_form(str(fname)) for fname in fnames]
Out[35]: ['NFD', 'NFC']

```
 * this allows me to check that in my archives, all files use either 'NFC' or 'NFD':

```python
In [41]: np.unique([get_form(str(fname)) for fname in sorted(Path('/home/data').glob('**/*'))])
Out[42]: array(['NFC', 'NFD', 'NFKD'], dtype='<U4')

```


```python
for fname in sorted(Path('/home/data').glob('**/*')):
    fname_str = str(fname)
    if is_utf(fname_str):
        if unicodedata.is_normalized('NFKD', fname_str): print(fname_str)

```


  * if it is, does it exist in two versions?

```python
forms = ['NFD', 'NFC']
def check_other_forms(fname):
   form = get_form(fname)
   for other_form in forms:
      if not other_form == form:
          other_fname = unicodedata.normalize(other_form, fname)
          if Path(other_fname).is_file():
            print(f'File {fname=} is in {form=} and also exists in  {other_fname=} in {other_form=}')

In : [check_other_forms(str(fname)) for fname in fnames]

```
 
  * we can use [filecmp](https://docs.python.org/3/library/filecmp.html) to compare these files
```python
forms = ['NFD', 'NFC']
import filecmp
def check_other_forms(fname):
   form = get_form(fname)
   for other_form in forms:
      if not other_form == form:
          other_fname = unicodedata.normalize(other_form, fname)
          if Path(other_fname).is_file():
            print(f'File {fname=} is in {form=} and also exists in  {other_fname=} in {other_form=}')
            if filecmp.cmp(fname, other_fname):
                print('<<< These are identical >>>')
            else:
                print('>>> These are different <<<')

[check_other_forms(str(fname)) for fname in fnames]

```


  * Let's simplify as we have only two forms, such that we have three cases
  
```python
norm_form, other_form = 'NFC', 'NFD'
import filecmp
def check_other_forms(fname):

   is_norm = Path(unicodedata.normalize(norm_form, fname)).is_file()
   is_other = Path(unicodedata.normalize(other_form, fname)).is_file()
   other_fname = unicodedata.normalize(other_form, fname)
   
   if is_norm and not is_other:
      print(f'File {fname=} is in {norm_form=} and does not exist in {other_form=}, do nothing.')
   elif is_norm and is_other:
      print(f'File {fname=} is in {norm_form=} and does exist in {other_form=}.')
      if filecmp.cmp(fname, other_fname):
          print('<<< These are identical - one should remove the other form >>>')
      else:
          print('>>> These are different - WARNING !! <<<')
   elif not is_norm and is_other:
      print(f'File {fname=}  does not exist in {norm_form=} but does in {other_form=}, renaming to {other_fname=}.')
   else:
       print ('This should not happen')
          
[check_other_forms(str(fname)) for fname in fnames]

```

  * Let's apply this to the results of a glob pattern as we have only two forms, such that we have three cases:


```python
norm_form, other_form = 'NFC', 'NFD'
import filecmp
def scan_other_forms(fnames):
    for fname in fnames:
        fname = str(fname)
        if not is_utf(fname):
            print(f'File {fname=} is NOT utf, skipping')
        else:
            is_norm = Path(unicodedata.normalize(norm_form, fname)).is_file()
            is_other = Path(unicodedata.normalize(other_form, fname)).is_file()
            other_fname = unicodedata.normalize(other_form, fname)
   
            if is_norm and not is_other:
                print(f'File {fname=} is in {norm_form=} and does not exist in {other_form=}, do nothing.')
            elif is_norm and is_other:
                print(f'File {fname=} is in {norm_form=} and does exist in {other_form=}.')
                if filecmp.cmp(fname, other_fname):
                    print('<<< These are identical - one should remove the other form >>>')
                else:
                    print('>>> These are different - WARNING !! <<<')
            elif not is_norm and is_other:
                print(f'File {fname=}  does not exist in {norm_form=} but does in {other_form=}, renaming to {other_fname=}.')
            else:
                print ('This should not happen')
          
path, pattern = '.', 'Qui*'
scan_other_forms(sorted(Path(path).glob(pattern)))
path, pattern = '.', '**/*'
scan_other_forms(sorted(Path(path).glob(pattern)))

```



  * finally, one can [remove / unlink](https://docs.python.org/3.9/library/pathlib.html#pathlib.Path.unlink) the identical file in the other form
```python

def dedup(path, pattern, dry_run=True):

    fnames = sorted(Path(path).glob(pattern))

    for fname in fnames:
        fname_str = str(fname)
        if is_utf(fname_str):

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
                        Path(other_fname).unlink()
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
          
path, pattern = '.', 'Qui*'
dedup(path, pattern)

path, pattern = '.', '**/*'
dedup(path, pattern)

```
  
  * a more general function handling also for other forms that people may have on their disk:

```python
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

```
  
  * using [shutil](https://docs.python.org/3/library/shutil.html#shutil.move) is more robust with directories

  * but there is a problem appearing when changing the name of a directory. A solution is to compute the depth of each file and to start from the first to the last   https://github.com/laurentperrinet/utf-dedup/commit/0ea8d8f4d2824871e9d17bd72273ba177ba86312


```python
import os 
def get_depth(fname, sep='/'):
   return len(os.path.normpath(fname).split(sep))
get_depth('/Users/laurentperrinet/quantic/timeline/2021-04-23_PhDProgram-course-in-computational-neuroscience/SpiNNaker/CNT_notebook.ipynb'), get_depth('/Users/laurentperrinet/quantic/timeline/2021-04-23_PhDProgram-course-in-computational-neuroscience/SpiNNaker/'), get_depth('/Users/laurentperrinet/quantic/timeline/2021-04-23_PhDProgram-course-in-computational-neuroscience/SpiNNaker')
```
  
  
