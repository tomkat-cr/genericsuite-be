"""
Password Encryption module
"""
from werkzeug.security import generate_password_hash, check_password_hash

from genericsuite.config.config import Config

settings = Config()


class Passwords:
    """ Class to handle all passwords operations """

    def encrypt_password(self, passcode: str) -> str:
        """
        Encrypts a password using the 'scrypt' method.
        :param passcode: The password to encrypt.
        :return: The encrypted password.
        """
        return generate_password_hash(
            settings.APP_SECRET_KEY + passcode,
            method='scrypt',
        )

    def verify_password(self, db_user_password: str,
                        form_auth_password: str) -> bool:
        """
        Verifies a password by comparing the encrypted form of
        the form_auth_password with the db_user_password.
        :param db_user_password: The encrypted password stored in the database.
        :param form_auth_password: The password entered by the user.
        :return: True if the passwords match, False otherwise.
        """
        return check_password_hash(
            db_user_password,
            settings.APP_SECRET_KEY + form_auth_password
        )

    def passwords_encryption(self, data: dict, password_fields: list) -> dict:
        """
        Apply encryption to fields listed as password fields.

        Args:
            datad (dict): The original record containing the unencrypted
            password fields.
            password_fields (list): The list of password fields to
            be encrypted.

        Returns:
            dict: The updated record with encrypted password fields.
        """
        for field in password_fields:
            if field in data:
                data[field] = self.encrypt_password(data[field])
        return data
