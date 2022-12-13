# Acknowledgements
Snowcrypt stands on the shoulders of giants.

Many tools for decrypting Audible files already exist.
FFMPEG of course can handle it.
Several options (open- and closed-source) are just a frontend for FFMPEG.

A couple have even written indepentant implementations,
such as Mbucari in C# as [AAXClean](https://github.com/Mbucari/AAXClean).
These were an invaluable asset while creating snowcrypt.

The original code base and algorithm for snowcrypt
was written in Java and ported to Python by github user BlindWanderer.
They posted it in response to [this](https://github.com/mkb79/Audible/issues/36) issue.

# Abstract
snowcrypt a pure Python decryption of Audible's .aax and .aaxc file format.
snowcrypt can only decrypt files for which you have a valid license.

# Why not just use FFMPEG?
In a word: simplicity.
FFMPEG is a wonderful tool from great developers.
Unfortunately, it's also somewhat fragmented in it's version install base,
so often the first instruction is "make sure you have X.X version installed."
With snowcrypt, you don't have to worry about any of that.
If you can install Python (which is MUCH easier),
you can install and use snowcrypt.

Note:
If you're looking for speed, FFMPEG is the better option.
Overall, snowcrypt is between half and a third as fast as FFMPEG.


# Installation

Install through pip
```
pip install snowcrypt
```

Install from source
```
git clone https://github.com/snowskeleton/snowcrypt.git
cd snowcrypt
pip install -U .
```

# Run without installing
You can run snowcrypt without installing,
by calling the `pyi_entrypoint.py` file with python.
Useful for development.
```
git clone https://github.com/snowskeleton/snowcrypt.git
cd snowcrypt
python pyi_entrypoint.py <arguments>
```

# AAXC
snowcrypt expects that `.aaxc` files will be accompanied by a matching `.voucher` file.
This happens automatically when downloading through [audible-cli](https://github.com/mkb79/audible-cli).
```
snowcrypt audioFile.aaxc
```

# AAX
Audible's older file format `.aax` uses a slightly different method of encryption. To decrypt it, you'll need the activation bytes unique to your account. 
You can obtain this value with mkb79's [audible-cli](https://github.com/mkb79/audible-cli) tool.
```
snowcrypt audioFile.aax -b <activationBytes>
```

# Import to other projects
```
from snowcrypt import snowcrypt
key, iv = snowcrypt.deriveKeyIV('input_file.aax', 'activation_bytes')
snowcrypt.decrypt_aaxc(
  'input_file.aax', 
  'output_file.m4a',
  key,
  iv)
```
