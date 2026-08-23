@no_type_check
def decrypt(secret, hash, data):
    """
    Decrypt per telegram docs at https://core.telegram.org/passport.

    Args:
        secret (:obj:`str` or :obj:`bytes`): The encryption secret, either as bytes or as a
            base64 encoded string.
        hash (:obj:`str` or :obj:`bytes`): The hash, either as bytes or as a
            base64 encoded string.
        data (:obj:`str` or :obj:`bytes`): The data to decrypt, either as bytes or as a
            base64 encoded string.
        file (:obj:`bool`): Force data to be treated as raw data, instead of trying to
            b64decode it.

    Raises:
        :class:`PassportDecryptionError`: Given hash does not match hash of decrypted data.

    Returns:
        :obj:`bytes`: The decrypted data as bytes.

    """
    if not CRYPTO_INSTALLED:
        raise RuntimeError(
            "To use Telegram Passports, PTB must be installed via `pip install "
            '"python-telegram-bot[passport]"`.'
        )
    # Make a SHA512 hash of secret + update
    digest = Hash(SHA512(), backend=default_backend())
    digest.update(secret + hash)
    secret_hash_hash = digest.finalize()
    # First 32 chars is our key, next 16 is the initialisation vector
    key, init_vector = secret_hash_hash[:32], secret_hash_hash[32 : 32 + 16]
    # Init a AES-CBC cipher and decrypt the data
    cipher = Cipher(AES(key), CBC(init_vector), backend=default_backend())
    decryptor = cipher.decryptor()
    data = decryptor.update(data) + decryptor.finalize()
    # Calculate SHA256 hash of the decrypted data
    digest = Hash(SHA256(), backend=default_backend())
    digest.update(data)
    data_hash = digest.finalize()
    # If the newly calculated hash did not match the one telegram gave us
    if data_hash != hash:
        # Raise a error that is caught inside telegram.PassportData and transformed into a warning
        raise PassportDecryptionError(f"Hashes are not equal! {data_hash} != {hash}")
    # Return data without padding
    return data[data[0] :]