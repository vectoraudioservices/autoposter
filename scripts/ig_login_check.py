import sys
from post_instagram import ig_login_test

if __name__ == "__main__":
    try:
        msg = ig_login_test()
        print(msg)
        sys.exit(0)
    except Exception as e:
        print(f"LOGIN ERROR: {e}")
        sys.exit(1)
