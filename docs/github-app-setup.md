# GitHub App Setup: Publishing to a Different Repository

This guide walks through creating or updating a GitHub App so it has permission to push content (releases, assets, commits, etc.) to a target repository that is different from the source repository.

---

## 1. Create a New GitHub App

If you do not yet have a GitHub App, follow these steps.

### 1.1 Navigate to App Settings

1. Go to **GitHub.com** and sign in.
2. Click your profile photo (top-right) > **Settings**.
3. In the left sidebar, scroll down and click **Developer settings**.
4. Click **GitHub Apps** > **New GitHub App**.

### 1.2 Fill in the App Details

| Field | Value |
|---|---|
| GitHub App name | A unique name, e.g. `my-deploy-bot` |
| Homepage URL | Your project URL or repository URL |
| Webhook | Uncheck "Active" if you do not need webhooks |

### 1.3 Set Repository Permissions

Under **Permissions > Repository permissions**, set the following based on what the app needs to do:

| Permission | Level | When needed |
|---|---|---|
| Contents | Read & write | Push commits, upload release assets |
| Metadata | Read-only | Required for all repo access |
| Pull requests | Read & write | Open/update pull requests |
| Releases | Read & write | Create or update releases |
| Actions | Read & write | Trigger workflows |

> Only grant the minimum permissions required.

### 1.4 Set Where the App Can Be Installed

Under **Where can this GitHub App be installed?**, choose:
- **Only on this account** - if the target repo is in the same org/account.
- **Any account** - if the target repo is in a different org or owned by someone else.

### 1.5 Create the App

Click **Create GitHub App**. You will be redirected to the app's settings page.

---

## 2. Generate a Private Key

The app needs a private key to authenticate as itself.

1. On the app's settings page, scroll down to **Private keys**.
2. Click **Generate a private key**.
3. A `.pem` file will be downloaded automatically. Store this securely - it is the app's credential.

Note the **App ID** displayed at the top of the settings page. You will need it alongside the private key.

---

## 3. Install the App on the Target Repository

Installing the app grants it access to specific repositories.

### 3.1 Install from the App Settings Page

1. On the app's settings page, click **Install App** in the left sidebar.
2. Click **Install** next to the account or organization that owns the **target repository**.
3. On the installation screen, choose:
   - **All repositories** - grants access to every repo in that account.
   - **Only select repositories** - recommended. Select only the specific target repo.
4. Click **Install**.

After installation, note the **Installation ID** from the URL:
```
https://github.com/settings/installations/<INSTALLATION_ID>
```

### 3.2 Install on a Repository in a Different Organization

If the target repo belongs to a different GitHub organization:

1. The app must have **"Any account"** selected in its installation setting (see step 1.4).
2. Share the app's public link with the org owner, or navigate to:
   ```
   https://github.com/apps/<app-slug>/installations/new
   ```
3. The org owner installs it and selects the target repository.

---

## 4. Update an Existing GitHub App

If you already have a GitHub App and need to add access to a new repository:

### 4.1 Update Permissions (if needed)

1. Go to **Settings > Developer settings > GitHub Apps**.
2. Click **Edit** on your app.
3. Under **Permissions & events**, update the repository permissions as needed.
4. Click **Save changes**.
5. GitHub will notify all existing installations about the permission change. Each installation owner must **approve** the new permissions before they take effect.

### 4.2 Add the New Repository to an Existing Installation

1. Go to **Settings > Applications > Installed GitHub Apps** (or the org's settings if it is an org installation).
2. Click **Configure** next to the app.
3. Under **Repository access**, add the new target repository to the list.
4. Click **Save**.

---

## 5. Authenticate as the App in Your Workflow

Use the private key and app credentials to generate a short-lived installation token.

### 5.1 Using the `actions/create-github-app-token` Action (Recommended for GitHub Actions)

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Generate app token
        id: app-token
        uses: actions/create-github-app-token@v1
        with:
          app-id: ${{ secrets.APP_ID }}
          private-key: ${{ secrets.APP_PRIVATE_KEY }}
          # Specify the owner of the target repo
          owner: target-org-or-user

      - name: Push to target repository
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
        run: |
          git clone https://x-access-token:$GH_TOKEN@github.com/target-org/target-repo.git
          cd target-repo
          # ... make changes ...
          git push
```

### 5.2 Store Credentials as Repository Secrets

In the **source** repository (the one running the workflow):

1. Go to **Settings > Secrets and variables > Actions**.
2. Add:
   - `APP_ID` - the numeric App ID from step 2.
   - `APP_PRIVATE_KEY` - the full contents of the `.pem` file.

---

## 6. Verify Access

After installation and configuration, verify the app has access:

```bash
# Using GitHub CLI (gh) with the generated token
GH_TOKEN=<installation-token> gh repo view target-org/target-repo

# Or test a write operation
GH_TOKEN=<installation-token> gh release create v1.0.0 --repo target-org/target-repo
```

---

## 7. Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `Resource not accessible by integration` | App not installed on target repo | Install the app on the target repo (step 3) |
| `Permission denied` | Missing or insufficient permissions | Update app permissions (step 4.1) and approve the change |
| `JWT token invalid` | Wrong App ID or malformed private key | Check that `APP_ID` and `APP_PRIVATE_KEY` secrets are correct |
| Token works on source repo but not target | Installation is scoped to source repo only | Reconfigure installation to include target repo (step 4.2) |
| Org requires approval for third-party apps | Org policy blocks unapproved apps | Org owner must approve the app under org settings |

---

## Summary Checklist

- [ ] GitHub App created with correct repository permissions
- [ ] Private key generated and stored securely
- [ ] App installed on the **target** repository (not just the source)
- [ ] Installation ID noted
- [ ] `APP_ID` and `APP_PRIVATE_KEY` added as secrets in the source repo
- [ ] Workflow uses `actions/create-github-app-token` or equivalent to generate a token
- [ ] Token passed to git/gh commands targeting the correct repo
