import sys
from post_instagram import ig_login_test

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts\\ig_login_check_client.py <ClientKey>")
        print("Example: python scripts\\ig_login_check_client.py Luchiano")
        sys.exit(1)
    client = sys.argv[1].strip()
    try:
        print(ig_login_test(client_name=client))
        sys.exit(0)
    except Exception as e:
        print(f"LOGIN ERROR ({client}): {e}")
        sys.exit(1)
