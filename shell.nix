with (import <nixpkgs> {});
mkShell {
  allowUnfree = true;

  nativeBuildInputs = [
    chromedriver
    curl
    direnv
    google-chrome
    jq
    python39
    python39Packages.selenium
    stdenv.cc.cc.lib
  ];

  shellHook = ''
    eval "$(direnv hook bash)"

    # If the Nix Python package has been gc'ed, remake the links to the current
    # Nix Python package.
    if [ ! -d "./venv39" ]; then
      echo "[!] Python create"
      python -m venv "./venv39/"
    fi

    if [ ! -e "./venv39/bin/python" ]; then
      echo "[!] Python upgrade"
      rm -f ./venv39/bin/python*
      python -m venv --upgrade ./venv39/
    fi

    . ./venv39/bin/activate

    python -m pip install -r requirements.txt 2>/dev/null
  '';

  # Unset PYTHONPATH to avoid polluting the virtual environment with system
  # Python packages.
  PYTHONPATH = "";
}
