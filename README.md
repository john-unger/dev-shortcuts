# dev-shortcuts

This repo contains various shortcuts I tend to make use of.

## 🖥🍏 macOS Install
Add these lines to your `.zshrc`:

```
# add zfuncs to fpath, and then lazy autoload
# every file in there as a function
fpath=(~/[path-to-repo]/zfuncs $fpath);
autoload -U $fpath[1]/*(.:t)
```
