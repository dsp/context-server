{
  description = "python context-servers";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python311;
        projectDeps = ps: with ps; [
          anyio # Add your Python dependencies here
          pip
        ];
        pythonEnv = python.withPackages projectDeps;
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            pythonEnv
            pkgs.rye
            pkgs.ruff
            pkgs.pyright
          ];
          shellHook = ''
            export PYTHONPATH=${pythonEnv}/${python.sitePackages}:$PYTHONPATH
          '';
        };
      });
}
