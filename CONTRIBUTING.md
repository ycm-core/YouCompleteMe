# Updating `index.html`

1. Check out this branch in a _new repo directory_, or use 
   [git-new-workdir][git-new-workdir]. You will need the original `README.md` as
   source for the generation. For example, if your YCM repo is in
   `./Development/YouCompleteMe`:

    ```bash
        $ git new-workdir Development/YouCompleteMe Development/YouCompleteMe-website
    ```

2. Install the required Python packages. It is recommended to do this with
   [virtualenv][]:

    ```bash
        $ virtualenv ~/Virtualenvs/ycm-website
        $ source ~/Virtualenvs/ycm-website/bin/activate
        (ycm-website)$ pip install -r requirements.txt
    ```

3. Run the generator script, passing it the path to the YCM `README.md`.
   Continuing the example, this would be done as follows:

    ```bash
        (ycm-website)$ cd Development/YouCompleteMe-website
        (ycm-website)$ ./update_from_readme.py ../YouCompleteMe/README.md
    ```

The command prints nothing if it succeeds. Check the output with `git status`
(etc.) then submit a PR to the YouCompleteMe project with the generated changes.

[git-new-workdir]: http://nuclearsquid.com/writings/git-new-workdir/
[virtualenv]: https://virtualenv.readthedocs.org/en/latest/
