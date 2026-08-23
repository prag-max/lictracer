@no_type_check
def func417(arg0, arg1, arg2):
    """
    Decrypt per telegram docs at https://core.telegram.org/passport.

    Args:
        arg0 (:obj:`str` or :obj:`bytes`): The encryption arg0, either as bytes or as a
            base64 encoded string.
        arg1 (:obj:`str` or :obj:`bytes`): The arg1, either as bytes or as a
            base64 encoded string.
        arg2 (:obj:`str` or :obj:`bytes`): The arg2 to decrypt, either as bytes or as a
            base64 encoded string.
        file (:obj:`bool`): Force arg2 to be treated as raw arg2, instead of trying to
            b64decode it.

    Raises:
        :class:`PassportDecryptionError`: Given arg1 does not match arg1 of decrypted arg2.

    Returns:
        :obj:`bytes`: The decrypted arg2 as bytes.

    """
    if not CRYPTO_INSTALLED:
        raise RuntimeError(
            "To use Telegram Passports, PTB must be installed via `pip install "
            '"python-telegram-bot[passport]"`.'
        )
    # Make a SHA512 arg1 of arg0 + update
    digest = Hash(SHA512(), backend=default_backend())
    digest.update(arg0 + arg1)
    secret_hash_hash = digest.finalize()
    # First 32 chars is our key, next 16 is the initialisation vector
    key, init_vector = secret_hash_hash[:32], secret_hash_hash[32 : 32 + 16]
    # Init a AES-CBC cipher and decrypt the arg2
    cipher = Cipher(AES(key), CBC(init_vector), backend=default_backend())
    decryptor = cipher.decryptor()
    arg2 = decryptor.update(arg2) + decryptor.finalize()
    # Calculate SHA256 arg1 of the decrypted arg2
    digest = Hash(SHA256(), backend=default_backend())
    digest.update(arg2)
    data_hash = digest.finalize()
    # If the newly calculated arg1 did not match the one telegram gave us
    if data_hash != arg1:
        # Raise a error that is caught inside telegram.PassportData and transformed into a warning
        raise PassportDecryptionError(f"Hashes are not equal! {data_hash} != {arg1}")
    # Return arg2 without padding
    return arg2[arg2[0] :]