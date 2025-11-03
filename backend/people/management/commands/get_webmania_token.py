from django.core.management.base import BaseCommand
import requests
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Fetch Webmania API token using WEBMANIA_APP_KEY and WEBMANIA_APP_SECRET. Optionally write to backend/.env with --write'

    def add_arguments(self, parser):
        parser.add_argument('--write', action='store_true', help='Write token to backend/.env (creates file if missing)')
        parser.add_argument('--cep-url', default='https://webmaniabr.com/api/1/cep/', help='Webmania base CEP URL (for token endpoint override)')

    def handle(self, *args, **options):
        app_key = getattr(settings, 'WEBMANIA_APP_KEY', None) or os.getenv('WEBMANIA_APP_KEY')
        app_secret = getattr(settings, 'WEBMANIA_APP_SECRET', None) or os.getenv('WEBMANIA_APP_SECRET')
        if not app_key or not app_secret:
            self.stderr.write('WEBMANIA_APP_KEY and WEBMANIA_APP_SECRET must be set in settings or environment')
            return

        # Note: Webmania does not appear to provide a token exchange endpoint for these CEP calls in public docs.
        # However some accounts may accept a GET to /api/1/cep/<cep> with app_key/app_secret query params.
        # There is no documented token endpoint, so this command will attempt a harmless call to /api/1/cep/01001-000/ to validate keys.
        test_cep = '01001-000'
        url = options.get('cep_url').rstrip('/') + f'/{test_cep}/'
        params = {'app_key': app_key, 'app_secret': app_secret}
        self.stdout.write(f'Attempting to validate app_key/app_secret via {url} ...')
        try:
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                self.stdout.write(self.style.SUCCESS('App key/secret validated successfully (request OK).'))
                # Webmania may not return a token; inform the user and exit
                self.stdout.write('Webmania did not return a token endpoint; use panel to get a token if needed.')
                # Optionally, if service returned a token field, display it
                try:
                    data = r.json()
                    # look for token-like keys
                    for k in ('access_token','token','api_token'):
                        if k in data:
                            token = data.get(k)
                            self.stdout.write(self.style.SUCCESS(f'Found token in response key "{k}": {token}'))
                            if options.get('write'):
                                self._write_env_token(token)
                            return
                except Exception:
                    pass
                return
            else:
                self.stderr.write(f'Validation request failed: {r.status_code} {r.text[:200]}')
                return
        except Exception as exc:
            self.stderr.write(f'Error calling Webmania: {exc}')
            return

    def _write_env_token(self, token):
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '..', '..', '.env')
        env_path = os.path.normpath(env_path)
        # fallback to backend/.env in project root
        if not os.path.exists(os.path.dirname(env_path)):
            os.makedirs(os.path.dirname(env_path), exist_ok=True)
        # read existing .env if any
        content = ''
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()
        lines = content.splitlines()
        found = False
        for i,l in enumerate(lines):
            if l.strip().startswith('WEBMANIA_API_TOKEN='):
                lines[i] = f'WEBMANIA_API_TOKEN={token}'
                found = True
                break
        if not found:
            lines.append(f'WEBMANIA_API_TOKEN={token}')
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines)+('\n' if lines and not lines[-1].endswith('\n') else ''))
        self.stdout.write(self.style.SUCCESS(f'Wrote WEBMANIA_API_TOKEN to {env_path}'))

