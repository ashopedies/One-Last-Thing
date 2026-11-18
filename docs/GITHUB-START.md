# First upload to GitHub

GitHub keeps your addon code, its change history and downloadable versions. Your friend installs a published release; they do not need the development tools or tests.

The two packages serve different purposes:

- **OneLastThing-0.14.5-forever.zip**: install this in WoW or share it directly.
- **OneLastThing-0.14.5-source.zip**: use this to create your GitHub repository. It includes the addon, documentation, tests and release automation.

Both include **CHANGELOG.md**, an ordinary text file you can open without GitHub. GitHub also displays it as a readable page.

## 1. Create your repository

1. Create a GitHub account and install GitHub Desktop from https://desktop.github.com/.
2. In GitHub Desktop, choose **File > New repository**. Name it **OneLastThing**, choose a local folder, and create it. Do not generate another license or README; these are included.
3. Extract the **source ZIP** into that repository folder. README.md, CHANGELOG.md, OneLastThing, tools and tests belong directly inside it. Make sure the hidden **.github** folder was also copied; it contains the automation.
4. Return to GitHub Desktop. Review the files, enter a summary such as `Initial One Last Thing release`, then choose **Commit to main**.
5. Choose **Publish repository**. Make it public if you want a publicly accessible download/update feed. This step publishes your files to GitHub; it is not done automatically by this package.

No game account files, SavedVariables, downloaded third-party addon databases or personal paths are included in the source ZIP.

## 2. Publish the first downloadable release

1. Open your repository on GitHub. In the **Actions** tab, check that the checks workflow succeeds.
2. Open **Releases > Draft a new release**. Create the tag **v0.14.5**, targeting your main branch, and use **One Last Thing 0.14.5** as its title.
3. Copy the 0.14.5 notes from CHANGELOG.md into the description and publish the release.
4. The tag starts the release workflow. Wait for it to succeed under **Actions**. It adds **OneLastThing-0.14.5-forever.zip** to the release assets. Until that asset appears, the install package is not ready.
5. If automation is disabled or fails, the already supplied install ZIP can be uploaded manually to that release. Keep the `-forever.zip` filename. GitHub's automatic “Source code” downloads are not the game installation ZIP.

The workflow also supports running **Release > Run workflow** with the same tag to retry packaging. It tests before publishing the install asset.

## 3. Give your friend one link

Send the GitHub **repository URL**, for example `https://github.com/YOUR-NAME/OneLastThing` with your actual username. In WowUp, choose the Forever client and install from that URL, then enable updates as desired.

A direct download link to one ZIP is useful for manual installation, but does not provide an ongoing update feed. See the provider instructions: https://wowup.io/guide/get-addons/overview.

## 4. Publish later updates

1. Update the code and test it in WoW.
2. Increase the version in Core.lua, both main TOC files and the addon README.txt.
3. Add the new entry at the top of the root CHANGELOG.md and copy that changelog into OneLastThing/CHANGELOG.md.
4. Commit the changes in GitHub Desktop and push them.
5. Create a new release/tag such as **v0.14.3**. Never reuse an old version for a different published update. The workflow runs tests, checks the versions agree and attaches the new install ZIP.

Simply pushing code does not publish a new install release. Your friend's updater sees the next published release after that release has its install asset. No separate message with every ZIP is necessary.

## Optional local checks

With Python installed, run these from the repository folder:

```sh
python3 -m pip install -r requirements-dev.txt
python3 tests/test_addon.py
python3 tools/package.py --version 0.14.5
```

Windows installations may use `py` instead of `python3`. The generated install ZIP appears in dist/. The checks simulate WoW APIs and cannot confirm the live client or third-party database coverage.
