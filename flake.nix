{
  description = "A python development flake";
  inputs.nixpkgs = {
    url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };
  inputs.flake-utils = {
    url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        makePkgs =
          {
            overlays ? [ ],
          }:
          import nixpkgs {
            inherit system;
            overlays = [
              # (final: prev: {
              # })
            ]
            ++ overlays
            ++ [
              # (final: prev: {
              # })
            ];
          };
        makeCommonPackages = { pkgs }: [ ];
        makeScripts = { pkgs }: [ ];
        makeCommonShell = { pkgs }: { };
      in
      {
        devShells = {
          default =
            let
              pkgs = makePkgs {
                overlays = [ ];
              };
              scripts = makeScripts { inherit pkgs; };
              commonPackages = makeCommonPackages { inherit pkgs; };
              commonShell = makeCommonShell { inherit pkgs; };
            in
            pkgs.mkShell (
              commonShell
              // {
                packages =
                  commonPackages
                  ++ scripts
                  ++ [
                    pkgs.python313
                    pkgs.black
                    pkgs.mypy
                    pkgs.pre-commit
                    pkgs.pylint
                    pkgs.uv
                  ];
              }
            );
        };
      }
    );
}
