from django import forms


class EmailForm(forms.Form):
    email = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'usuario@dominio.com'}))

from django import forms


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


