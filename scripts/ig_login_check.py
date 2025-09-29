import sys
from post_instagram import ig_login_test

def main():
    if len(sys.argv) < 2:
        print("Usage: ig_login_check_client.py <ClientName>")
        sys.exit(2)

    client = sys.argv[1]
    result = ig_login_test(client)
    if result["ok"]:
        print(f"LOGIN OK ({client}) via {result['via']} -> @{result['username']} (user_id={result['user_id']})")
        sys.exit(0)
    else:
        if result.get("two_factor"):
            print(f"LOGIN 2FA NEEDED ({client}): {result['error']}")
            sys.exit(3)
        else:
            print(f"LOGIN ERROR ({client}): {result['error']}")
            sys.exit(1)

if __name__ == "__main__":
    main()

