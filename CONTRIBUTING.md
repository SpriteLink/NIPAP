# Contributing to NIPAP

Looking to contribute to NIPAP? Contributions to NIPAP are very welcome -
**here's how you can help**!

Please take a moment to review this document in order to make the contribution
process easy and effective for everyone involved.


## Issues

As a user of NIPAP it is possible you may hit bugs or find areas that need
improvement. Please report any bugs or improvement requests through GitHub's
issues on [the GitHub issue page](http://github.com/SpriteLink/NIPAP/issues).

One of the easiest and best ways to start contributing is by simply giving
input on existing issues. How do you think a bug should be solved or how should
a new feature be designed to give you the most use? Go through a few issues and
comment!

If you would like to submit code, you are welcome to do so by submitting a Pull
Request. Start by reading through our guidelines on [code submission](#code-submission).

Please **do not** use the issue tracker for support issues. Use IRC or Google+.


### Bug report

A bug is a demonstrable problem that is caused by the code in the repository.
Good bug reports are extremely helpful, so thanks!

Guidelines for bug reports:

1. **Use the GitHub issue search** &mdash; check if the issue has already been
   reported.

2. **Check if the issue has been fixed** &mdash; try to reproduce it using the
   latest `master` or development branch in the repository and/or search closed
   issues.


### Feature requests

Feature requests are welcome. But take a moment to find out whether your idea
fits with the scope and aims of the project. We are pretty open to feature
ideas, just make sure you provide as much detail and context as possible.


## Code submission

Since NIPAP is hosted on GitHub, the most common method for sending code is
through a pull request (PR).

Submitting code is a fantastic help to this project. However, **before**
writing some piece of code and submitting as a PR, please use IRC, Google+ or
[open an issue](#create-an-issue) to discuss your bug fix, feature enhancement or
similar so that your ideas align with the project, otherwise you risk working
on something that the project's developers might not want to merge into the
project.

Your workflow should probably look something like this:

1. [Fork](http://help.github.com/fork-a-repo/) the project, clone your fork and
   configure the remotes:

   ```bash
   # Clone your fork of the repo into the current directory
   git clone https://github.com/<your-username>/NIPAP.git
   # Navigate to the newly cloned directory
   cd NIPAP
   # Assign the original repo to a remote called "upstream"
   git remote add upstream https://github.com/SpriteLink/NIPAP.git
   ```

2. If you cloned a while ago, get the latest changes from upstream:

   ```bash
   git checkout master
   git pull upstream master
   ```

3. Create a new topic branch (off the main project development branch) to
   contain your feature, change, or fix. Remember to name your branch
   [something useful](#branch-naming):

   ```bash
   git checkout -b <topic-branch-name>
   ```

4. Commit your changes in logical chunks that adhere to [our commit
   guidelines](#writing-history).

5. Locally merge (or rebase) the upstream development branch into your topic branch:

   ```bash
   git pull [--rebase] upstream master
   ```

6. Push your topic branch up to your fork:

   ```bash
   git push origin <topic-branch-name>
   ```

7. Make sure your code passes our [automated test suite](#travis-ci).

8. [Open a Pull Request](https://help.github.com/articles/using-pull-requests/)
   with a clear title and description against the `master` branch.

**IMPORTANT**: By submitting a patch, you agree to allow the project owners to
license your work under the terms of the [MIT License](LICENSE).


### Create an issue

Please try to create an issue on GitHub to track the **problem** you are
seeing. The code in your PR is your proposed **solution** to the problem. If
your PR is rejected, we can still keep track of the **problem** if there is an
issue opened for that.

It is better discussing potential solutions in an issue than in PRs as PRs are
commonly closed and another PR is opened with an updated patch. The issue will
keep it all in one place.


### Writing history

Read these [git commit message
guidelines](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html)
on writing good commit messages.

The git history of PRs tend to become cluttered in the feedback cycle before
acceptance of a PR. Remember that you are writing history (pun intended) and we
strive to keep a clean git commit history. Use rebasing to squash out
intermediate commits and write **one** or a few commit messages that makes
sense for the patch.

See [git rebase](https://github.com/SpriteLink/NIPAP/wiki/git-rebase) for more
information on rebasing.

If you are submitting a very large patch, possibly affecting multiple
components, it might we worthwhile to consider splitting the patch into several
pieces (several PRs). It is important though that each PR handles a distinct
change on its own. There is no point in splitting a patch into smaller ones if
the smaller pieces do not, on their own, bring any benefit.


### branch naming

Don't name your branches
* enhancements
* some-bugfix

Instead, use something like;
* backend-add-ipv8
* 123-fix-cli-traceback

Preferably adding the reference to the issue here on GitHub, like in the last
example.

If you want, you can also structure your branches within "namespaces";
* cli/123-fix-traceback
* web/1337-fix-css


### Version numbering
Try not to bump version numbers in your patch to add functionality X. By the
time your PR is accepted, we might already have increased the version number
(making your patch obsolete) or there is a need to commit more new features
before releasing a new version OR your new version is so cool that it requires
a major version bump. Anyway, please let the project maintainers handle the
versioning and instead focus on your code :)


### Travis-CI
Travis-CI is a continuous integration platform that tests the codebase of a
project every time a new commit is pushed to GitHub. NIPAP uses Travis-CI to
prevent unwanted side-effects of code changes.

Make sure that the unittests run fine (you can do this locally) and that
Travis-CI runs fine with your patch (this will be visible at the bottom of the
PR page on GitHub).


### License

By contributing your code, you agree to license your contribution under the
[MIT license](LICENSE).
