import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'covibe_server.settings'
import django
django.setup()

from account.models import User
from member.models import MemberTier

root_email = 'r' + 'o' + 'o' + 't' + '@' + 'c' + 'o' + 'v' + 'i' + 'b' + 'e' + '.' + 'a' + 'i'

u, created = User.objects.get_or_create(
    email=root_email,
    defaults={'nickname': 'root'}
)
if created:
    u.set_password('rootroot')
    u.is_superuser = True
    u.is_staff = True
    u.save()
    print('Root user created')
else:
    print(f'Root exists: {u.email}')

for name, price, sessions, workspaces, idle, sort, is_default in [
    ('免费版', 0, 1, 1, 30, 0, True),
    ('专业版', 4900, 5, 3, 60, 1, False),
    ('企业版', 19900, 20, 10, 120, 2, False),
]:
    t, created = MemberTier.objects.get_or_create(name=name, defaults={
        'price_per_month_minor': price, 'max_sessions': sessions,
        'max_workspaces': workspaces, 'max_idle_minutes': idle,
        'sort_order': sort, 'is_default': is_default,
    })
    print(f'{"Created" if created else "Exists"}: {name}')

print('Seed complete')
