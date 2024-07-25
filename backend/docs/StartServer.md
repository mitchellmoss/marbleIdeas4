
## DO THIS FIRST
1. cd backend
2. source backend-env/bin/activate
3. pip install -r requirements.txt
   

## How To Start Production Server
gunicorn --workers=4 --bind=0.0.0.0:8000 wsgi:app
### ADMIN PASSWORD

1. Set the ADMIN_PASSWORD environment variable for the admin dashboard /admin route


Here's the rewritten version in markdown:

```markdown
# Removing Files Already in Version Control After Adding to .gitignore

Files and folders already tracked by Git won't automatically be removed from the repository just because you've added them to `.gitignore`. They are already in the repository and need to be manually removed. Here's how you can do it:

> **Important:** Remember to commit all your changes before proceeding with these steps!

To remove all files from the repository and add them back (this time respecting the rules in your `.gitignore`), use these commands:

```bash
git rm -rf --cached .
git add .
```

This process:
1. Removes all files from Git's index (but keeps them in your working directory)
2. Re-adds all files, now respecting your `.gitignore` rules

After running these commands, files that should be ignored (as per your `.gitignore`) will no longer be tracked by Git.
```

## CREATE requirements.txt
pip freeze > requirements.txt