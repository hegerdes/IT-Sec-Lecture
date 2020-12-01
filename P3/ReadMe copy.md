# Info to P3

## Info P3.1
I created a md file with the commands I used for P3.1
**Content:**

```bash
gpg --full-generate-key
>RSA and RSA
>Len    4096
>Name   MyName
>Mail   MyMail
>Okay

#Add additional uids
gpg --edit-key <key-id>
# Export to add to key server
gpg --export --armor hegerdes@uni-osnabrueck.de > hegerdes.pub

# Revoca key
gpg --generate-revocation hegerdes@uni-osnabrueck.de

# Add sys-lehre key
gpg --receive-keys 64E2C6380E941015

```

## Info P3.2
I created client and server as robust as possible but it is hard without knowing the exact test settings.

I opted for default PW in the Server file.
I tested it with su and GUI interface.

The script userhandler.sh helped. With ```sudo ./userhandler.sh add``` it creates a new user called tmp and logs in.  ```sudo ./userhandler.sh del``` removes the user tmp.

The *.py files have some constantes like:
 * Hardcodes PW = MySecretPW
 * REC_BUFFER_SIZE = 4098
 * SET_TRUST = True
 * VERBOSE = FALSE