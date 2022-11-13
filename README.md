# snowcrypt

snowcrypt is a tool to decrypt audible files for which you have a valid license.

Install through pip
```
pip install snowcrypt
```



and use like so

# AAXC
snowcrypt expects that `.aaxc` files will be accompanied by a matching `.voucher` file.
This happens automatically when downloading through [audible-cli](https://github.com/mkb79/audible-cli).
```
snowcrypt audioFile.aaxc
```

# AAX
Audible's older file format `.aax` uses a slightly different method of encryption. To decrypt it, you'll need the activation bytes unique to your account. 
```
snowcrypt audioFile.aax -b XXXXXXXX
```
where the X's are the activation bytes for your account.
You can obtain this value with mkb79's [audible-cli](https://github.com/mkb79/audible-cli) tool.
