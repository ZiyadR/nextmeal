import os
import sys
import secrets

# Ensure we're running from the root directory
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
backend_dir = os.path.join(root_dir, 'backend')

sys.path.insert(0, backend_dir)

# Change working directory to backend so alembic.ini is found correctly
os.chdir(backend_dir)

def main():
    print("="*60)
    print(" NextMeal - Automated Production Setup ")
    print("="*60)
    print("\nPlease paste your Supabase Connection String (URI).")
    print("It should look like: postgres://postgres.[ref]:[password]@.../postgres\n")
    
    import re
    db_url = input("DATABASE_URL: ").strip()
    
    if not db_url:
        print("Error: DATABASE_URL cannot be empty.")
        sys.exit(1)
        
    # Extract just the URL in case the user accidentally pasted extra text
    match = re.search(r'(postgres(?:ql)?://[^\s]+)', db_url)
    if match:
        db_url = match.group(1)
    else:
        print("Error: Could not find a postgres:// or postgresql:// URL in your input.")
        sys.exit(1)
        
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    from urllib.parse import quote, unquote
    scheme_end = db_url.find('://')
    if scheme_end != -1:
        scheme = db_url[:scheme_end+3]
        rest = db_url[scheme_end+3:]
        pieces = rest.rsplit('@', 1)
        if len(pieces) == 2:
            user_pass, host_rest = pieces
            user_pass_parts = user_pass.split(':', 1)
            if len(user_pass_parts) == 2:
                user, raw_pass = user_pass_parts
                raw_pass = unquote(raw_pass)
                encoded_pass = quote(raw_pass, safe="")
                db_url = f"{scheme}{user}:{encoded_pass}@{host_rest}"

    if not db_url.startswith("postgresql://"):
        print("Error: It doesn't look like a valid PostgreSQL URL.")
        sys.exit(1)
        
    # Set it in the environment so Alembic and the App pick it up
    os.environ["DATABASE_URL"] = db_url
    
    print("\n[1/3] Running Database Migrations...")
    try:
        from alembic.config import Config
        from alembic import command
        
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations completed.")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    
    print("\n[2/3] Seeding Initial Data...")
    try:
        from app.seed_data import seed_database
        seed_database()
        print("✅ Seeding completed.")
    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        sys.exit(1)
    
    print("\n[3/3] Generating Secure Keys...")
    secret_key = secrets.token_urlsafe(32)
    
    print("\n" + "="*60)
    print(" 🎉 SETUP COMPLETE! You are ready to deploy to Vercel.")
    print("="*60)
    print("\nWhen importing this repository into Vercel, expand the")
    print("'Environment Variables' section and copy-paste the following:\n")
    
    print(f"Name:  DATABASE_URL")
    print(f"Value: {db_url}\n")
    
    print(f"Name:  SECRET_KEY")
    print(f"Value: {secret_key}\n")
    
    print(f"Name:  FRONTEND_ORIGINS")
    print(f"Value: *\n")
    
    print("Note: Setting FRONTEND_ORIGINS to '*' is safe on Vercel since")
    print("both the frontend and backend share the exact same domain.")
    print("="*60)

if __name__ == "__main__":
    main()
