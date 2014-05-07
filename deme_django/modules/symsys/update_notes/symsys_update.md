# Steps to update

- ./manage.py migrate

- edit `Symsys Website Layout`, update CSS link


--- dev notes:
if forget password, ./manage.py shell

from cms.models import *
x = AllToAllPermission.objects.get(ability="login_as")
x.is_allowed = True
x.save()
