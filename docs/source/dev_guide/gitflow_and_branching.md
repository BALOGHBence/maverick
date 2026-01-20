# GitFlow and Branching Strategy

The adopted GitFlow is the following:

1) You decide to work on implementing a new feature called 'new_feature'.
2) You open a feature branch based on the `dev` branch with the naming convention `feature/<the_name_of_the_feature>`, which in this case would be 'feature/new_feature'.
3) You test your contribution locally, commit your changes and push to the feature branch.
4) You open a PR to `dev`. This triggers some GitHub actions responsible to run tests. If the test pass, code has the required quality, the PR is accepted to `dev`.
5) When a number of new features are to be published, we open a PR from `dev` to `main`. This triggers testing again. If all is good, a test deployment is done to TestPyPI.
6) If all is good, we bump the version number and create a new release. This triggers a GitHub Action that publishes to PyPI.

Notes

- If what you are working on is not a new feature but a **fix**, the branch you open should have the naming convention `fix/<the_name_of_the_issue>`.
- If what you are working on is not a new feature but a **hotfix**, the branch you open should have the naming convention `hotfix/<the_name_of_the_issue>`.
