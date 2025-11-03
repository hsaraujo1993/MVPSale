import os
import sys


def main():
    # Usage: python backend/tools/list_routes.py [settings_module]
    settings = sys.argv[1] if len(sys.argv) > 1 else "MVPSale.settings.dev"
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings)

    import django
    from django.urls import URLResolver, URLPattern, get_resolver

    django.setup()

    def iter_patterns(patterns, prefix=""):
        for p in patterns:
            if isinstance(p, URLResolver):
                new_prefix = prefix + str(p.pattern)
                yield from iter_patterns(p.url_patterns, new_prefix)
            elif isinstance(p, URLPattern):
                yield prefix + str(p.pattern), p.name

    resolver = get_resolver()
    routes = list(iter_patterns(resolver.url_patterns))
    for path, name in sorted(routes):
        print(f"{path}\t{name or ''}")


if __name__ == "__main__":
    main()

