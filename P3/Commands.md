# P3.1 Commands

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