# Abstract

snowcrypt is a tool to decrypt audible files for which you have a valid license.

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
