# Contributing
Any contributions to NIPAP are very much welcome. As a user of NIPAP it is possible you may hit bugs or find areas that need improvement. Please report any bugs or improvement requests through GitHub's issues on [the GitHub issue page](http://github.com/SpriteLink/NIPAP/issues). If you would like to submit code, try to read through our guidelines below first.

If you are uncertain on your bug/improvement issue, don't hesitate to discuss it on the official NIPAP IRC channel - #NIPAP on freenode.

## Code submission

Since NIPAP is hosted on GitHub, the most common method for sending code is through a pull request (PR). We have no principal problem with PRs - it's just that they tend to become cluttered with changes in a number of commits as feedback is given on the initial patch. We want PRs with a clean commit history. 

## Create an issue
Please try to create an issue here on GitHub to track the _problem_ you are seeing. The PR is your proposed _solution_ to the problem. If your PR is rejected, we can still keep track of the _problem_ if there is an issue opened for that.

It is better discussing potential solutions in an issue than in PRs as PRs are commonly closed and another PR is opened with an updated patch. The issue can keep it all in one place.


## Descriptive  branch naming
Don't name your branches
* enhancements
* some-bugfix

Instead, use something like;
* backend-add-ipv8
* 123-fix-cli-traceback

Preferably adding the reference to the issue here on GitHub, like in the last example.

If you want, you can also structure your branches within "namespaces";
* cli/123-fix-traceback
* web/1337-fix-css


## Travis-CI
Travis-CI is a continuous integration platform that tests the codebase of a project every time a new commit is pushed to GitHub. NIPAP uses Travis-CI to prevent unwanted side-effects of code changes.

Make sure that the unittests run fine (you can do this locally) and that Travis-CI runs fine with your patch (this will be visible at the bottom of the PR page on GitHub).


## Git log
A PR is submitted for implementation of X. Feedback is left in the form of comments on the PR. Author updates patch according to feedback and pushes updated code to the PR. Git log is now filled with crap.

We strive to keep a clean git log and so instead of just updating the PR, rebase to squash out intermediate commits and write _one_ commit message that makes sense for the patch. See [git rebase](https://github.com/SpriteLink/NIPAP/wiki/git-rebase) for more information.


## Big patches and multiple components
If you are submitting a very large patch, possibly affecting multiple components, it might we worthwhile to consider splitting the patch into several pieces (several PRs). It is important though that each PR handles a distinct change on its own. There is no point in splitting a patch into smaller ones if the smaller pieces do not, on their own, bring any benefit.


## Version numbering
Try not to bump version numbers in your patch to add functionality X. By the time your PR is accepted, we might already have increased the version number (making your patch obsolete) or there is a need to commit more new features before releasing a new version OR your new version is so cool that it requires a major version bump. Anyway, please let the project maintainers handle the versioning and instead focus on your code :)
