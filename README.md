# dev-shortcuts

This repo contains various shortcuts I tend to make use of.

## 🖥🍏 macOS Install

This is to lazyload all the scripts into the terminal, to allow autocomplete, and also a helper function to reload all the scripts (to avoid sourcing existing terminals)
Add these lines to your `.zshrc`:

```

# add zfuncs to fpath, and then lazy autoload
export DEV_SHORTCUTS_ROOT="$HOME/Documents/dev-shortcuts"

ZFUNCS_DIR="$DEV_SHORTCUTS_ROOT/zfuncs"
fpath=("$ZFUNCS_DIR" $fpath)

zfuncs-init() {
  emulate -L zsh
  setopt extendedglob

  # Always (re)register function files for autoload
  autoload -Uz $ZFUNCS_DIR/*(.:t)

  # Initialize completion once per shell (cheap if already initialized)
  autoload -Uz compinit
  compinit -i

  # Optional: only do heavier stuff when explicitly requested
  case "${1:-}" in
    rehash|refresh)
      rehash
      # Re-run compinit to refresh completion dump immediately
      compinit -i
      ;;
  esac
}

# Run the lightweight setup at shell start
zfuncs-init

# Manual refresh command when you add/remove scripts
zfuncs-rehash() { zfuncs-init rehash }

```
