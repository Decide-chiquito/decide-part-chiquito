from django import forms
from django.contrib.auth.models import User
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509 import NameOID

class EmailForm(forms.Form):
    email = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'usuario@dominio.com'}))

class PasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': '********'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': '********'}))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        # Verificar que las contraseñas coincidan
        if password and confirm_password and password != confirm_password:
            self.add_error('password', 'Las contraseñas no coinciden.')
            self.add_error('confirm_password', 'Las contraseñas no coinciden.')

        # Verificar si la contraseña cumple con ciertos criterios (puedes personalizar esto)
        if password and len(password) < 8 and len(self.errors) == 0:
            self.add_error('password', 'La contraseña debe tener al menos 8 caracteres.')

        # Verificar si la contraseña es lo suficientemente fuerte según tus criterios
        if password and len(self.errors) == 0:
            if not any(char.isdigit() for char in password) and len(self.errors) == 0:
                self.add_error('password', 'La contraseña debe contener al menos un número.')

            elif not any(char.isupper() for char in password) and len(self.errors) == 0:
                self.add_error('password', 'La contraseña debe contener al menos una letra mayúscula.')

            elif not any(char.islower() for char in password) and len(self.errors) == 0:
                self.add_error('password', 'La contraseña debe contener al menos una letra minúscula.')

            elif not any(char in "!@#$%^&*()-_=+[]{}|;:'\",.<>?/" for char in password) and len(self.errors) == 0:
                self.add_error('password', 'La contraseña debe contener al menos un carácter especial.')

        return cleaned_data



class CertificateLoginForm(forms.Form):
    cert_file = forms.FileField(label='Certificate File', required=True)
    cert_password = forms.CharField(label='Certificate Password', widget=forms.PasswordInput, required=True)

    def get_or_create_user(self):
        try:
            if not self.is_valid():
                return None

            cert_content = self.cleaned_data['cert_file'].read()
            cert_password = self.cleaned_data['cert_password']

            _, cert, additional_certs = pkcs12.load_key_and_certificates(cert_content, cert_password.encode('utf-8'), backend=default_backend())

            cert_json = {
                'subject': cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value,
            }


            if '-' in cert_json['subject']:
                subject_name = cert_json['subject'].split('-')[0].strip()
            else:
                subject_name = cert_json['subject'].strip()

            user, _ = User.objects.get_or_create(username=subject_name)

            return user

        except Exception:
            return None


