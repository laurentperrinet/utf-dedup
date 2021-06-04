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


### solving the problem

* Let's [glob](https://docs.python.org/3.9/library/pathlib.html#pathlib.Path.glob) some files:

```python

from pathlib import Path
path, pattern = '..', '**/Qui*'
for fname in Path(path).glob(pattern): print(fname)
fname, fname2 = sorted(Path('.').glob('Qui*'))
```

The “**” pattern means “this directory and all subdirectories, recursively”. In other words, it enables recursive globbing.

* we will cycle over all globed file and do the following:
 * is the file  name coded in utf?

```python
def is_utf(fname):
   return fname == fname.encode('ascii', 'replace').decode("utf-8")
is_utf(str(fname))
```
